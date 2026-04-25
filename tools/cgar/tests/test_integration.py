"""
Integration tests for CGARResolver.
Tests the CGAR stages in isolation from Docker/MEMRES by mocking them.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch, call

from src.constraint_store import ConstraintStore, ConstraintType
from src.candidate_graph_builder import CandidateGraphBuilder
from src.constraint_solver import ConstraintSolver
from src.failure_injector import FailureInjector


def test_solver_skips_assignment_injected_as_failed():
    """
    End-to-end: solver picks assignment → failure injected → next call skips it.
    """
    store = ConstraintStore(soft_threshold=1)
    solver = ConstraintSolver(store)
    injector = FailureInjector(store)

    graph = {
        'numpy': [
            {'version': '1.24.3', 'requires_python': '>=3.8', 'requires_dist': []},
            {'version': '1.21.6', 'requires_python': '>=3.7', 'requires_dist': []},
        ]
    }

    # First solve → picks 1.24.3
    first = solver.solve(graph, '3.8')
    assert first['numpy'] == '1.24.3'

    # Simulate ImportError on first assignment
    injector.inject(first, '3.8', 'ImportError: numpy failed', 'ImportError')

    # Second solve → should skip 1.24.3 (soft threshold=1 → now infeasible)
    second = solver.solve(graph, '3.8', exclude_combo=first)
    assert second is not None
    assert second['numpy'] == '1.21.6'


def test_constraint_store_persists_across_solver_calls():
    """Constraints learned in one snippet inform subsequent snippets."""
    store = ConstraintStore()
    # Snippet A fails: tensorflow 1.15.5 on Python 2.7
    store.add('tensorflow', '1.15.5', '2.7', ConstraintType.HARD,
              "requires Python >=3.6", 1.0)

    # Snippet B: solver should skip tensorflow 1.15.5
    solver = ConstraintSolver(store)
    graph = {
        'tensorflow': [
            {'version': '1.15.5', 'requires_python': None, 'requires_dist': []},
            {'version': '2.9.0', 'requires_python': None, 'requires_dist': []},
        ]
    }
    result = solver.solve(graph, '2.7')
    assert result['tensorflow'] != '1.15.5'

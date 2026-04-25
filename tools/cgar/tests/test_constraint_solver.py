import pytest
from src.constraint_solver import ConstraintSolver
from src.constraint_store import ConstraintStore, ConstraintType


def _make_graph(packages_versions: dict) -> dict:
    """Helper: build a simple candidate graph from {pkg: [ver1, ver2, ...]}."""
    return {
        pkg: [{'version': v, 'requires_python': None, 'requires_dist': []} for v in versions]
        for pkg, versions in packages_versions.items()
    }


def test_solver_finds_valid_assignment():
    graph = _make_graph({'numpy': ['1.24.3', '1.21.6'], 'scipy': ['1.10.1', '1.7.3']})
    store = ConstraintStore()
    solver = ConstraintSolver(store)
    result = solver.solve(graph, python_version='3.8')
    assert result is not None
    assert 'numpy' in result
    assert 'scipy' in result


def test_solver_skips_infeasible_version():
    graph = _make_graph({'numpy': ['1.24.3', '1.21.6']})
    store = ConstraintStore()
    store.add('numpy', '1.24.3', '3.8', ConstraintType.HARD, 'build-fail', 1.0)
    solver = ConstraintSolver(store)
    result = solver.solve(graph, python_version='3.8')
    assert result is not None
    assert result['numpy'] == '1.21.6'


def test_solver_returns_none_when_all_versions_infeasible():
    graph = _make_graph({'numpy': ['1.24.3', '1.21.6']})
    store = ConstraintStore()
    store.add('numpy', '1.24.3', '3.8', ConstraintType.HARD, 'x', 1.0)
    store.add('numpy', '1.21.6', '3.8', ConstraintType.HARD, 'x', 1.0)
    solver = ConstraintSolver(store)
    result = solver.solve(graph, python_version='3.8')
    assert result is None


def test_solver_prefers_newest_version():
    graph = _make_graph({'pandas': ['2.0.3', '1.3.5', '0.24.2']})
    store = ConstraintStore()
    solver = ConstraintSolver(store)
    result = solver.solve(graph, python_version='3.8')
    assert result['pandas'] == '2.0.3'


def test_solver_empty_candidates_for_unknown_package():
    # Package with no PyPI candidates → no version pinned (pass-through)
    graph = {'flotilla': []}
    store = ConstraintStore()
    solver = ConstraintSolver(store)
    result = solver.solve(graph, python_version='3.8')
    # flotilla gets no pin, but solver succeeds with empty string
    assert result is not None
    assert result.get('flotilla', '') == ''


def test_solver_next_assignment_skips_bad_combo():
    graph = _make_graph({
        'tensorflow': ['1.15.5', '2.9.0'],
        'numpy': ['1.16.6', '1.24.3'],
    })
    store = ConstraintStore()
    # First call → picks newest
    solver = ConstraintSolver(store)
    first = solver.solve(graph, python_version='2.7')
    assert first is not None
    # Mark that assignment as bad combo
    store.add_combo(first, '2.7', 'ImportError: cannot import name', 0.9)
    # Second call → finds different assignment
    second = solver.solve(graph, python_version='2.7', exclude_combo=first)
    assert second != first or second is None  # Either different or exhausted

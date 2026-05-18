"""
PlannerAgent — picks candidate version assignments.

Role: select a (package -> version) assignment that is likely feasible,
given the shared ConstraintStore's accumulated knowledge of past failures.

Tools:
    - query_pypi(packages, python_version)  -> candidate graph (live PyPI metadata)
    - wheel_filter(graph)                    -> graph pruned to wheel-available versions
    - solve(graph, exclude_combo)            -> consistent assignment via backtracking

The Planner is the only agent that READS from the ConstraintStore to
filter candidates. It does not write constraints itself — that's the
Analyzer's job.
"""

from typing import Dict, List, Optional

from .base_agent import Agent
from ..candidate_graph_builder import CandidateGraphBuilder
from ..constraint_solver import ConstraintSolver


class PlannerAgent(Agent):
    """Plans the next version assignment to try."""

    role = "Planner"

    def __init__(self, store, logger=None, pypi_timeout: int = 8):
        super().__init__(store, logger)
        self.graph_builder = CandidateGraphBuilder(timeout=pypi_timeout)
        self.solver = ConstraintSolver(store)
        self.state["plans_made"] = 0

    def _tool_names(self) -> List[str]:
        return ["query_pypi", "wheel_filter", "solve"]

    # ── Tools ────────────────────────────────────────────────────────

    def query_pypi(self, packages: List[str], python_version: str) -> Dict[str, list]:
        """Fetch candidate versions for each package from live PyPI."""
        self.log(f"query_pypi({packages}, py={python_version})")
        return self.graph_builder.build_graph(packages, python_version)

    def wheel_filter(self, graph: Dict[str, list]) -> Dict[str, list]:
        """Filter the candidate graph to wheel-available versions only.

        Note: CandidateGraphBuilder already performs wheel filtering inside
        get_candidates(), sorting wheel-available versions first. This method
        is a transparent wrapper that makes the wheel-filter step explicit
        in the agent pipeline (matches slide's tool list).
        """
        # Pass-through: wheel filtering happens inside graph_builder
        return graph

    def solve(self, graph: Dict[str, list], python_version: str,
              exclude_combo: Optional[Dict[str, str]] = None
              ) -> Optional[Dict[str, str]]:
        """Run constraint solver over the candidate graph.

        Returns assignment dict or None if solver exhausted.
        """
        assignment = self.solver.solve(graph, python_version, exclude_combo=exclude_combo)
        if assignment is None:
            self.log("solver exhausted")
        return assignment

    # ── Lifecycle ────────────────────────────────────────────────────

    def step(self, packages: List[str], python_version: str,
             exclude_combo: Optional[Dict[str, str]] = None
             ) -> Optional[Dict[str, str]]:
        """Run one planning step: query_pypi -> wheel_filter -> solve."""
        self.state["plans_made"] += 1

        graph = self.query_pypi(packages, python_version)
        graph = self.wheel_filter(graph)

        for pkg, cands in graph.items():
            self.log(f"  {pkg}: {len(cands)} candidates from PyPI")

        assignment = self.solve(graph, python_version, exclude_combo=exclude_combo)
        if assignment is not None:
            self.log(f"assignment: {assignment}")
        return assignment

"""
CGARResolver — Main orchestrator for CGAR tool.

Wraps MEMRES EnhancedResolver, inserting Stages 2.5 and 2.6 between
MEMRES's module cleaning (Stage 2) and its version-selection cascade (Stage 3).

On each Docker failure, FailureInjector converts the error into a constraint,
and the solver is re-run to find the next viable assignment (counterfactual
backtracking) before falling back to the original MEMRES cascade.
"""

import os
import sys
import time
from typing import Dict, List, Optional

# Resolve memres src path: mounted at /memres_src in Docker,
# relative path locally for development
_MEMRES_SRC = os.environ.get('MEMRES_SRC_PATH',
    os.path.join(os.path.dirname(__file__), '..', '..', 'memres', 'src'))
if os.path.exists(_MEMRES_SRC) and _MEMRES_SRC not in sys.path:
    sys.path.insert(0, os.path.abspath(_MEMRES_SRC))

from .constraint_store import ConstraintStore, ConstraintType
from .candidate_graph_builder import CandidateGraphBuilder
from .constraint_solver import ConstraintSolver
from .failure_injector import FailureInjector


class CGARResolver:
    """
    CGAR-enhanced resolver.

    Adds to EnhancedResolver:
    - Stage 2.5: CandidateGraphBuilder (live PyPI metadata)
    - Stage 2.6: ConstraintSolver (backtracking with learned constraints)
    - Stage 2.7: FailureInjector (Docker failure → constraint)
    - Stage 2.8: Counterfactual backtracking (re-solve before LLM fallback)

    The session-scoped ConstraintStore is shared across all snippets resolved
    by this instance, enabling cross-snippet transfer learning.

    NOTE: This class is a mixin/wrapper. The full orchestration (MEMRES pipeline
    integration) is done in enhanced_resolver_patched.py (Task 7). This class
    exposes the CGAR-specific stages and hooks as a standalone unit that can
    be tested and used independently.
    """

    def __init__(self, *args, **kwargs):
        self.constraint_store = ConstraintStore(soft_threshold=2)
        self.graph_builder = CandidateGraphBuilder(timeout=8)
        self.solver = ConstraintSolver(self.constraint_store)
        self.injector = FailureInjector(self.constraint_store)
        self._cgar_attempts = 0
        self._cgar_rescues = 0
        self._cgar_current_assignment: Optional[Dict[str, str]] = None
        self._cgar_fallback = False

    def _cgar_log(self, msg: str) -> None:
        """Log a CGAR-stage message. Uses parent log() if available."""
        if hasattr(self, 'log'):
            self.log(msg)
        else:
            print(msg, flush=True)

    def cgar_select_versions(self, packages: List[str],
                              python_version: str,
                              exclude_combo: Optional[Dict] = None) -> Optional[Dict[str, str]]:
        """
        Stage 2.5 + 2.6: Build candidate graph and solve for best assignment.
        Returns {package: version} or None if solver finds nothing viable.
        """
        self._cgar_log(f"  [CGAR] Building candidate graph for {packages} on Python {python_version}")
        graph = self.graph_builder.build_graph(packages, python_version)

        for pkg, candidates in graph.items():
            self._cgar_log(f"  [CGAR]   {pkg}: {len(candidates)} candidates from PyPI")

        assignment = self.solver.solve(graph, python_version, exclude_combo=exclude_combo)
        if assignment:
            self._cgar_log(f"  [CGAR] Solver assignment: {assignment}")
        else:
            self._cgar_log(f"  [CGAR] Solver exhausted — falling back to MEMRES cascade")
        return assignment

    def cgar_inject_failure(self, assignment: Dict[str, str], python_version: str,
                             error_log: str, error_type: str) -> None:
        """Stage 2.7: Convert Docker failure into ConstraintStore record."""
        self.injector.inject(assignment, python_version, error_log, error_type)
        self._cgar_log(f"  [CGAR] Constraint injected. Store stats: {self.constraint_store.stats()}")

    def cgar_select_packages_for_build(self, packages: Dict[str, str],
                                        python_version: str) -> Dict[str, str]:
        """
        Hook called before each Docker build attempt.
        CGAR overrides version selection for unversioned packages if solver
        finds a better assignment. Falls back to original packages if solver
        is exhausted.
        """
        if self._cgar_fallback:
            return packages

        # Only intervene for packages without pinned versions
        pkg_names = [p for p, v in packages.items() if not v]
        versioned = {p: v for p, v in packages.items() if v}

        if not pkg_names:
            return packages  # All already versioned — CGAR not needed

        self._cgar_attempts += 1
        cgar_assignment = self.cgar_select_versions(
            pkg_names, python_version,
            exclude_combo=self._cgar_current_assignment,
        )

        if cgar_assignment is None:
            self._cgar_fallback = True
            return packages

        self._cgar_current_assignment = cgar_assignment
        return {**versioned, **cgar_assignment}

    def cgar_on_build_failure(self, assignment: Dict[str, str], python_version: str,
                               error_log: str, error_type: str) -> None:
        """
        Hook called after each failed Docker attempt.
        Injects constraint so next solve skips this assignment.
        Also detects API-removed errors and adds upper bound constraints.
        """
        if not self._cgar_fallback and self._cgar_current_assignment:
            self.cgar_inject_failure(
                self._cgar_current_assignment, python_version, error_log, error_type
            )
            # Detect API-removed errors → inject upper bound for that package/version
            self.injector.inject_api_removed(
                self._cgar_current_assignment, python_version, error_log
            )

    def cgar_on_success(self) -> None:
        """Hook called on successful resolution."""
        self._cgar_rescues += 1
        self._cgar_log(
            f"  [CGAR] Session stats: "
            f"attempts={self._cgar_attempts}, "
            f"rescues={self._cgar_rescues}, "
            f"store={self.constraint_store.stats()}"
        )

    def cgar_reset_snippet(self) -> None:
        """Reset per-snippet state (call at start of each new snippet)."""
        self._cgar_current_assignment = None
        self._cgar_fallback = False

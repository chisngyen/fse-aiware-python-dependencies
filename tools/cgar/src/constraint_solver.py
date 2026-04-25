"""
ConstraintSolver — Stage 2.6

Backtracking solver over a candidate graph, consulting ConstraintStore to prune
known-infeasible assignments. Does not implement full PubGrub — uses simple
greedy backtracking sufficient for the scale of this problem (typically <10 packages).

Novel contribution: integrates ConstraintStore (learned from Docker failures)
into the version-selection search, enabling counterfactual backtracking without
re-running Docker.
"""

from typing import Dict, List, Optional

from .constraint_store import ConstraintStore


class ConstraintSolver:
    """
    Greedy backtracking solver.

    Algorithm:
    1. For each package, candidates are pre-sorted newest-first.
    2. Iterate candidates, skipping versions marked infeasible in ConstraintStore.
    3. Pick the first (newest) viable version per package independently.
    4. If the resulting combo is in ConstraintStore as a bad combo, backtrack
       on the last package and try its next candidate, etc.
    """

    def __init__(self, store: ConstraintStore):
        self.store = store

    def _viable_versions(self, package: str, candidates: List[Dict],
                         python_version: str) -> List[str]:
        """Return candidate versions not marked infeasible, preserving order."""
        result = []
        for c in candidates:
            ver = c['version']
            if ver and not self.store.is_infeasible(package, ver, python_version):
                result.append(ver)
        # Always include empty string as final fallback (unversioned install)
        result.append('')
        return result

    def solve(self, graph: Dict[str, List[Dict]], python_version: str,
              exclude_combo: Optional[Dict[str, str]] = None) -> Optional[Dict[str, str]]:
        """
        Find a compatible version assignment for all packages in graph.

        Returns Dict[package → version] or None if no viable assignment exists.
        `exclude_combo`: if provided, skip this exact assignment (used for
        counterfactual backtracking after a Docker failure).
        """
        packages = list(graph.keys())
        viable = {
            pkg: self._viable_versions(pkg, graph[pkg], python_version)
            for pkg in packages
        }

        # Check if any package has zero viable options (excluding empty fallback)
        for pkg in packages:
            if len(viable[pkg]) == 0:
                return None

        # Simple greedy: pick first viable for each package
        assignment = {pkg: viable[pkg][0] for pkg in packages}

        # If this combo is excluded or known-bad, find the next one
        if self._is_excluded(assignment, python_version, exclude_combo):
            assignment = self._next_assignment(
                packages, viable, python_version, exclude_combo
            )

        return assignment

    def _is_excluded(self, assignment: Dict[str, str], python_version: str,
                     exclude_combo: Optional[Dict[str, str]]) -> bool:
        if self.store.is_combo_infeasible(assignment, python_version):
            return True
        if exclude_combo and assignment == exclude_combo:
            return True
        return False

    def _next_assignment(self, packages: List[str],
                         viable: Dict[str, List[str]],
                         python_version: str,
                         exclude_combo: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """
        Enumerate assignments in order (vary last package fastest),
        skipping known-bad combos.
        """
        indices = {pkg: 0 for pkg in packages}

        def increment() -> bool:
            """Advance to next combination. Returns False if exhausted."""
            for i in range(len(packages) - 1, -1, -1):
                pkg = packages[i]
                if indices[pkg] + 1 < len(viable[pkg]):
                    indices[pkg] += 1
                    for j in range(i + 1, len(packages)):
                        indices[packages[j]] = 0
                    return True
            return False

        # Skip first (already tried)
        if not increment():
            return None

        max_attempts = 50  # Safety limit
        for _ in range(max_attempts):
            candidate = {pkg: viable[pkg][indices[pkg]] for pkg in packages}
            if not self._is_excluded(candidate, python_version, exclude_combo):
                return candidate
            if not increment():
                return None

        return None

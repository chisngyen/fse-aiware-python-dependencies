"""
AnalyzerAgent — converts Docker build failures into typed constraints.

Role: take a raw error log (and the assignment that caused it) and
extract structured knowledge that the Planner can use to prune the
search space on the next attempt.

Tools:
    - parse_error(error_log, assignment)        -> (ConstraintType, signature)
    - gen_constraint(assignment, py, log, type) -> write HARD/SOFT/UPPER to store

Classification (handled by FailureInjector.classify_error):
    HARD  — regex matches deterministic incompatibility
            ("requires a different Python", "No matching distribution", ...)
            -> cấm vĩnh viễn sau 1 quan sát.
    SOFT  — regex matches runtime errors (ImportError, ModuleNotFoundError, ...)
            -> cấm tạm thời, cần ≥ soft_threshold (=2) quan sát.
    UPPER — error log matches "cannot import name X from pkg"
            -> infer API was removed; cấm cả khoảng [current_version, ∞).
"""

from typing import Any, Dict, List, Tuple

from .base_agent import Agent
from ..constraint_store import ConstraintType
from ..failure_injector import FailureInjector, classify_error


class AnalyzerAgent(Agent):
    """Translates Docker failures into ConstraintStore entries."""

    role = "Analyzer"

    def __init__(self, store, logger=None):
        super().__init__(store, logger)
        self.injector = FailureInjector(store)
        self.state["constraints_added"] = 0
        self.state["upper_bounds_added"] = 0

    def _tool_names(self) -> List[str]:
        return ["parse_error", "gen_constraint"]

    # ── Tools ────────────────────────────────────────────────────────

    def parse_error(self, error_log: str,
                    assignment: Dict[str, str]) -> Tuple[ConstraintType, str]:
        """Classify the error log and produce a normalized signature.

        Returns:
            (constraint_type, signature) — type is HARD or SOFT.
            UPPER bounds are detected separately inside gen_constraint().
        """
        ctype, sig = classify_error(error_log, assignment)
        self.log(f"parse_error -> type={ctype.value}, sig={sig[:80]}")
        return ctype, sig

    def gen_constraint(self, assignment: Dict[str, str], python_version: str,
                       error_log: str, error_type: str) -> Dict[str, Any]:
        """Write constraint(s) extracted from this failure into the store.

        Adds HARD or SOFT (via FailureInjector.inject), plus optionally an
        UPPER bound if the log indicates API removal.

        Returns store stats after the write.
        """
        before = self.store.stats()
        self.injector.inject(assignment, python_version, error_log, error_type)
        self.injector.inject_api_removed(assignment, python_version, error_log)
        after = self.store.stats()

        # Track new additions for telemetry
        new_hard = after["hard"] - before["hard"]
        new_soft = after["soft"] - before["soft"]
        new_ub = after["upper_bounds"] - before["upper_bounds"]
        self.state["constraints_added"] += new_hard + new_soft
        self.state["upper_bounds_added"] += new_ub

        if new_ub:
            self.log(f"gen_constraint -> +UPPER bound; store={after}")
        elif new_hard:
            self.log(f"gen_constraint -> +HARD; store={after}")
        else:
            self.log(f"gen_constraint -> +SOFT (or count++); store={after}")
        return after

    # ── Lifecycle ────────────────────────────────────────────────────

    def step(self, assignment: Dict[str, str], python_version: str,
             error_log: str, error_type: str) -> Dict[str, Any]:
        """Run one Analyzer step: parse_error -> gen_constraint."""
        self.parse_error(error_log, assignment)
        return self.gen_constraint(assignment, python_version, error_log, error_type)

"""
CGARResolver — Multi-Agent Coordinator for CGAR.

Orchestrates four cooperating agents around a shared, session-scoped
ConstraintStore (matches the architecture diagram in the slide):

       ┌──────────┐  query_pypi     ┌──────────┐
       │ Planner  │ ──────────────> │ Executor │
       └────┬─────┘  wheel_filter   └────┬─────┘
            │  solve                     │ build_docker
            │                            │ run_import
            │                            ▼
            │                       ┌─────────┐
            │                       │ Docker  │
            │                       └────┬────┘
            │            ┌───────────────┘
            │            ▼ (fail)
            │       ┌──────────┐  parse_error      ┌──────────┐
            │       │ Analyzer │ ────────────────> │  Critic  │
            │       └────┬─────┘  gen_constraint   └────┬─────┘
            │            │                              │
            │            │ HARD / SOFT / UPPER          │ analyze_failures
            │            ▼                              │ suggest_strategy
            │     ┌──────────────┐                      │
            └─────│ Session Store│ ◀────────────────────┘
                  └──────────────┘

Communication is loose-coupled: each agent reads/writes the shared
ConstraintStore; no direct method calls between agents. The coordinator
(this class) handles the build loop and consults the Critic when stuck.

Backward-compatible hooks (cgar_select_packages_for_build,
cgar_on_build_failure, cgar_on_success, cgar_reset_snippet) are preserved
for integration with the MEMRES EnhancedResolver in
enhanced_resolver_patched.py.
"""

import os
import sys
from typing import Any, Dict, List, Optional

# Resolve memres src path: mounted at /memres_src in Docker,
# relative path locally for development.
_MEMRES_SRC = os.environ.get(
    "MEMRES_SRC_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "memres", "src"),
)
if os.path.exists(_MEMRES_SRC) and _MEMRES_SRC not in sys.path:
    sys.path.insert(0, os.path.abspath(_MEMRES_SRC))

from .constraint_store import ConstraintStore
from .agents import (
    PlannerAgent,
    ExecutorAgent,
    AnalyzerAgent,
    CriticAgent,
)


class CGARResolver:
    """Multi-Agent coordinator for Constraint-Guided Agentic Resolution.

    Composes four agents (Planner / Executor / Analyzer / Critic) over a
    shared ConstraintStore. Designed to be mixed into MEMRES
    ``EnhancedResolver`` via multiple inheritance (see
    ``enhanced_resolver_patched.py``); the resolver's existing Docker
    pipeline drives the actual build, while the agents take care of
    candidate selection and failure-to-constraint conversion.
    """

    def __init__(self, *args, **kwargs):
        # ── Shared session memory ─────────────────────────────────────
        self.constraint_store = ConstraintStore(soft_threshold=2)

        # ── Four agents ───────────────────────────────────────────────
        self.planner = PlannerAgent(self.constraint_store, logger=self._cgar_log)
        self.executor = ExecutorAgent(self.constraint_store, logger=self._cgar_log)
        self.analyzer = AnalyzerAgent(self.constraint_store, logger=self._cgar_log)
        self.critic = CriticAgent(self.constraint_store, logger=self._cgar_log)

        # ── Backwards-compat aliases (used by enhanced_resolver_patched
        #    and any external tooling that referenced the old attributes). ─
        self.graph_builder = self.planner.graph_builder
        self.solver = self.planner.solver
        self.injector = self.analyzer.injector

        # ── Per-session bookkeeping ───────────────────────────────────
        self._cgar_attempts = 0
        self._cgar_rescues = 0
        self._cgar_current_assignment: Optional[Dict[str, str]] = None
        self._cgar_fallback = False
        self._cgar_last_critic_suggestion: Optional[Dict[str, Any]] = None

    # ── Logging ──────────────────────────────────────────────────────

    def _cgar_log(self, msg: str) -> None:
        """Log via parent ``log`` if mixed into a resolver; else stdout."""
        parent_log = getattr(self, "log", None)
        if callable(parent_log) and parent_log is not self._cgar_log:
            parent_log(msg)
        else:
            print(msg, flush=True)

    # ── Multi-Agent API (matches slide vocabulary) ───────────────────

    def cgar_select_versions(self, packages: List[str], python_version: str,
                              exclude_combo: Optional[Dict[str, str]] = None
                              ) -> Optional[Dict[str, str]]:
        """Run the Planner agent to pick a version assignment."""
        return self.planner.step(
            packages, python_version, exclude_combo=exclude_combo
        )

    def cgar_inject_failure(self, assignment: Dict[str, str], python_version: str,
                             error_log: str, error_type: str) -> None:
        """Run the Analyzer agent on a Docker failure, then notify Critic."""
        self.analyzer.step(assignment, python_version, error_log, error_type)
        # Critic observes the failure (it decides for itself whether to fire)
        self.critic.record_failure(assignment, python_version, error_type)

    def cgar_consult_critic(self) -> Dict[str, Any]:
        """Run one Critic step. Fires only if stuck (≥3 same-type fails)."""
        suggestion = self.critic.step()
        self._cgar_last_critic_suggestion = suggestion
        return suggestion

    # ── Backwards-compat hooks (used by EnhancedResolver patches) ────

    def cgar_select_packages_for_build(self, packages: Dict[str, str],
                                        python_version: str) -> Dict[str, str]:
        """Hook called by EnhancedResolver before each Docker build.

        Routes through the Planner agent. If the Planner returns no
        assignment, CGAR falls back to MEMRES' original cascade and
        marks subsequent calls as fallback (no further intervention).
        """
        if self._cgar_fallback:
            return packages

        unversioned = [p for p, v in packages.items() if not v]
        versioned = {p: v for p, v in packages.items() if v}
        if not unversioned:
            return packages

        self._cgar_attempts += 1
        cgar_assignment = self.cgar_select_versions(
            unversioned, python_version,
            exclude_combo=self._cgar_current_assignment,
        )
        if cgar_assignment is None:
            self._cgar_fallback = True
            return packages

        self._cgar_current_assignment = cgar_assignment
        return {**versioned, **cgar_assignment}

    def cgar_on_build_failure(self, assignment: Dict[str, str], python_version: str,
                               error_log: str, error_type: str) -> None:
        """Hook called by EnhancedResolver after each failed build.

        Drives the Analyzer (extracts constraint) and optionally the
        Critic (if Planner appears stuck). The Critic's suggestion is
        stored on the resolver but acting on it (e.g. switching Python)
        is the responsibility of the outer build loop.

        Uses the caller-supplied ``assignment`` when CGAR has not yet
        picked one for this attempt (fallback path); otherwise prefers
        the Planner's own assignment so constraints stay attributed to
        the version combo the agent actually proposed.
        """
        effective = self._cgar_current_assignment or assignment
        if self._cgar_fallback or not effective:
            return

        self.cgar_inject_failure(
            effective, python_version, error_log, error_type
        )
        suggestion = self.cgar_consult_critic()
        if suggestion.get("action") != "continue":
            self._cgar_log(f"  [Critic] suggestion: {suggestion}")

    def cgar_on_success(self) -> None:
        """Hook called by EnhancedResolver when a snippet resolves."""
        self._cgar_rescues += 1
        self._cgar_log(
            "  [CGAR] session stats: "
            f"attempts={self._cgar_attempts}, "
            f"rescues={self._cgar_rescues}, "
            f"store={self.constraint_store.stats()}, "
            f"critic_activations={self.critic.state.get('activations', 0)}"
        )

    def cgar_reset_snippet(self) -> None:
        """Hook called by EnhancedResolver at the start of each new snippet.

        Resets per-snippet state in the coordinator and in the Critic
        (its failure history is per-snippet). The ConstraintStore is
        NOT reset — it persists across snippets in the same session.
        """
        self._cgar_current_assignment = None
        self._cgar_fallback = False
        self._cgar_last_critic_suggestion = None
        self.critic.reset()

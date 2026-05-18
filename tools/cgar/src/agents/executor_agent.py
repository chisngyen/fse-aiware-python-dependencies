"""
ExecutorAgent — runs Docker build / import validation.

Role: validate Planner's assignment by executing it inside a Docker
container. Returns success/fail + raw error log. The Executor is the
only agent that does NOT invoke an LLM — it is purely tool-driven.

Tools:
    - build_docker(python_version, packages)  -> invokes Docker build
    - run_import(snippet_path)                 -> import-only validation

The actual Docker pipeline lives in MEMRES's EnhancedResolver (in
enhanced_resolver_patched.py). This agent acts as a thin facade that
records the build attempt and surfaces a uniform interface. Concrete
build invocation is delegated to the parent resolver via a callback,
keeping the agent stateless w.r.t. Docker plumbing.
"""

from typing import Any, Callable, Dict, List, Optional

from .base_agent import Agent


class ExecutorAgent(Agent):
    """Executes Docker builds. Tool-only, no LLM."""

    role = "Executor"

    def __init__(self, store, logger=None,
                 build_callback: Optional[Callable[[str, Dict[str, str]], Any]] = None):
        """
        Args:
            store: Shared ConstraintStore.
            logger: Log callable.
            build_callback: Optional function(python_version, packages) -> result.
                If provided, called by build_docker(). Otherwise the actual
                build is delegated to the parent EnhancedResolver and this
                agent just records the attempt.
        """
        super().__init__(store, logger)
        self._build_callback = build_callback
        self.state["build_attempts"] = 0
        self.state["import_attempts"] = 0

    def _tool_names(self) -> List[str]:
        return ["build_docker", "run_import"]

    # ── Tools ────────────────────────────────────────────────────────

    def build_docker(self, python_version: str,
                     packages: Dict[str, str]) -> Dict[str, Any]:
        """Build a Docker image with the given Python + packages.

        If a build_callback was registered, it is invoked. Otherwise the
        call is delegated to the parent EnhancedResolver (this happens in
        practice because Docker plumbing lives in MEMRES).
        """
        self.state["build_attempts"] += 1
        self.log(f"build_docker(py={python_version}, "
                 f"pkgs={list(packages.keys())}) — attempt #{self.state['build_attempts']}")

        if self._build_callback is not None:
            return self._build_callback(python_version, packages)

        # Delegated to EnhancedResolver; caller orchestrates the actual build
        return {
            "delegated_to": "EnhancedResolver",
            "python_version": python_version,
            "packages": packages,
            "attempt": self.state["build_attempts"],
        }

    def run_import(self, snippet_path: str) -> Dict[str, Any]:
        """Run import-only validation on a snippet inside the build container.

        Used as a cheaper check than full execution. Delegated like build_docker.
        """
        self.state["import_attempts"] += 1
        self.log(f"run_import({snippet_path}) — attempt #{self.state['import_attempts']}")
        return {
            "delegated_to": "EnhancedResolver",
            "snippet_path": snippet_path,
            "attempt": self.state["import_attempts"],
        }

    # ── Lifecycle ────────────────────────────────────────────────────

    def step(self, python_version: str, packages: Dict[str, str]) -> Dict[str, Any]:
        """Execute one build attempt with the given assignment."""
        return self.build_docker(python_version, packages)

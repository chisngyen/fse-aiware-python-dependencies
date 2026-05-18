"""
Base Agent class for CGAR Multi-Agent architecture.

Each agent has three operational properties (matching the slide definition):
  1. role           — descriptive name, used for logging
  2. tools          — callable methods the agent uses to act
  3. state          — per-agent runtime state (reset between snippets)

All agents share a single ConstraintStore (session-scoped memory).
Communication between agents happens via reads/writes to this store,
not via direct method calls — this enables loose coupling.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class Agent(ABC):
    """Abstract base class for all CGAR agents."""

    #: Descriptive role name shown in logs (e.g. "Planner", "Executor").
    role: str = "AbstractAgent"

    def __init__(self, store, logger: Optional[Callable[[str], None]] = None):
        """
        Args:
            store: Shared ConstraintStore for cross-agent communication.
            logger: Optional callable for log messages. Defaults to print.
        """
        self.store = store
        self._logger = logger or print
        self.state: Dict[str, Any] = {}

    # ── Tool registry ────────────────────────────────────────────────

    @property
    def tools(self) -> List[str]:
        """Names of public tools this agent exposes.

        Subclasses override `_tool_names` to list their tools.
        """
        return list(self._tool_names())

    def _tool_names(self) -> List[str]:
        """Subclasses override to declare their tool method names."""
        return []

    # ── Lifecycle hooks ──────────────────────────────────────────────

    @abstractmethod
    def step(self, **kwargs) -> Any:
        """Execute one agent step. Subclasses implement.

        Returns whatever the agent produces (assignment, constraint, suggestion, …).
        """
        raise NotImplementedError

    def reset(self) -> None:
        """Reset per-snippet state. Called between snippets within a session.

        Subclasses may override to clear additional state. The shared
        ConstraintStore is NOT reset here — it persists across snippets
        in the same session.
        """
        self.state.clear()

    # ── Logging ──────────────────────────────────────────────────────

    def log(self, msg: str) -> None:
        """Emit a log line prefixed with the agent role."""
        if self._logger:
            self._logger(f"  [{self.role}] {msg}")

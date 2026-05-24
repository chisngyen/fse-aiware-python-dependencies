"""Method protocol shared by every methods/m*.py.

Importing _base is optional — methods can ignore it and just expose
``Method`` directly. But subclassing makes the contract explicit and
gives reasonable defaults for the harness to call.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from research.icse27._shared import (
    Blackboard, LLMBackbone, Snippet, TrajectoryLogger,
)


@dataclass
class Budget:
    """Wall-clock + retry budget enforced by the harness, not the method."""

    snippet_seconds: float = 300.0      # hard wall-clock per snippet
    k_build_max: int = 5                # max Docker build retries (matches CGAR HG2.9K)
    k_solve_max: int = 50               # max CSP attempts


@dataclass
class Resolution:
    """What every method must return from ``resolve()``.

    Schema mirrors the existing results.csv columns the harness writes.
    """

    passed: bool
    python_version: str = ""
    packages: list[str] = None          # type: ignore[assignment]
    result_tag: str = ""                # error tag or "None" for pass
    duration: float = 0.0
    extra: dict = None                  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.packages is None:
            self.packages = []
        if self.extra is None:
            self.extra = {}


class MethodProtocol(Protocol):
    """What every Method class must support. Type-checking aid only."""

    name: str
    contribution: str
    session_scope: bool      # True = blackboard kept across snippets

    def __init__(
        self,
        backbone: LLMBackbone | None,
        blackboard: Blackboard,
        tools: object,
        config: dict,
        trajectory: TrajectoryLogger,
    ) -> None: ...

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution: ...


class BaseMethod:
    """Optional convenience base. Methods can ignore and roll their own."""

    name: str = "unnamed"
    contribution: str = "(no claim recorded — G1 violation)"
    session_scope: bool = False

    def __init__(
        self,
        backbone: LLMBackbone | None,
        blackboard: Blackboard,
        tools: object,
        config: dict,
        trajectory: TrajectoryLogger,
    ) -> None:
        self.backbone = backbone
        self.bb = blackboard
        self.tools = tools
        self.config = config
        self.traj = trajectory

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        raise NotImplementedError("Method.resolve must be implemented")

"""Shared writable memory for multi-agent methods.

Superset of ``tools/cgar/src/constraint_store.py`` plus reflexion entries
and debate transcripts. Every agent reads and writes through this single
interface — no private state — so debates have a transparent evidence
trail and the trajectory log can capture cross-agent influence.

Disk format
-----------
``blackboard.jsonl`` — one JSON object per write. Append-only.
Replayable: a downstream analysis script can replay events to reconstruct
the blackboard at any point in time.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ConstraintKind(str, Enum):
    HARD = "hard"      # forbidden permanently (Python mismatch, no wheel, etc.)
    SOFT = "soft"      # forbidden after ≥2 confirmations
    UPPER = "upper"    # version must be < some bound (API-removed evidence)


@dataclass
class Constraint:
    package: str
    version: str | None    # specific version, or None for upper bound
    kind: ConstraintKind
    python_version: str | None = None
    upper_bound: str | None = None  # set when kind == UPPER
    evidence: str = ""              # one-line log excerpt that proved this
    source_agent: str = ""          # which agent emitted it
    confirmations: int = 1


@dataclass
class Reflection:
    snippet_id: str
    note: str                # short verbal lesson — "openai 1.x removes ChatCompletion"
    source_agent: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class DebateEntry:
    snippet_id: str
    agents: tuple[str, ...]
    topic: str               # e.g. "python_version" or "pkg:scipy"
    positions: dict[str, str]   # agent_name -> claim
    resolution: str = ""        # what the arbiter decided
    timestamp: float = field(default_factory=time.time)


class Blackboard:
    """Session-scoped store. Reset (or not) between snippets is method's choice."""

    def __init__(self, persist_path: Path | None = None) -> None:
        self.constraints: dict[tuple[str, str | None], Constraint] = {}
        self.reflections: list[Reflection] = []
        self.debates: list[DebateEntry] = []
        self.persist_path = persist_path
        if persist_path is not None:
            persist_path.parent.mkdir(parents=True, exist_ok=True)

    # ----- constraints ---------------------------------------------------

    def add_constraint(self, c: Constraint) -> None:
        key = (c.package, c.version)
        existing = self.constraints.get(key)
        if existing and existing.kind == c.kind:
            existing.confirmations += 1
        else:
            self.constraints[key] = c
        self._persist("constraint", c.__dict__)

    def is_blocked(self, package: str, version: str) -> bool:
        """True if the (package, version) is HARD-forbidden or SOFT-confirmed twice."""
        c = self.constraints.get((package, version))
        if c is None:
            return False
        if c.kind == ConstraintKind.HARD:
            return True
        if c.kind == ConstraintKind.SOFT and c.confirmations >= 2:
            return True
        return False

    def upper_bound_for(self, package: str) -> str | None:
        for (pkg, _), c in self.constraints.items():
            if pkg == package and c.kind == ConstraintKind.UPPER:
                return c.upper_bound
        return None

    # ----- reflections ---------------------------------------------------

    def add_reflection(self, r: Reflection) -> None:
        self.reflections.append(r)
        self._persist("reflection", {
            "snippet_id": r.snippet_id, "note": r.note,
            "source_agent": r.source_agent, "timestamp": r.timestamp,
        })

    def recent_reflections(self, n: int = 5) -> list[Reflection]:
        return self.reflections[-n:]

    # ----- debates -------------------------------------------------------

    def record_debate(self, d: DebateEntry) -> None:
        self.debates.append(d)
        self._persist("debate", {
            "snippet_id": d.snippet_id, "agents": list(d.agents),
            "topic": d.topic, "positions": d.positions,
            "resolution": d.resolution, "timestamp": d.timestamp,
        })

    # ----- stats for analysis -------------------------------------------

    def summary(self) -> dict:
        return {
            "n_constraints": len(self.constraints),
            "n_hard": sum(1 for c in self.constraints.values() if c.kind == ConstraintKind.HARD),
            "n_soft": sum(1 for c in self.constraints.values() if c.kind == ConstraintKind.SOFT),
            "n_upper": sum(1 for c in self.constraints.values() if c.kind == ConstraintKind.UPPER),
            "n_reflections": len(self.reflections),
            "n_debates": len(self.debates),
        }

    # ----- persistence ---------------------------------------------------

    def _persist(self, event_kind: str, payload: dict) -> None:
        if self.persist_path is None:
            return
        # ConstraintKind enum → string for JSON
        clean = {k: (v.value if isinstance(v, Enum) else v) for k, v in payload.items()}
        rec = {"kind": event_kind, "ts": time.time(), **clean}
        try:
            with self.persist_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, default=str) + "\n")
        except OSError:
            pass  # persistence is best-effort, never crashes the run

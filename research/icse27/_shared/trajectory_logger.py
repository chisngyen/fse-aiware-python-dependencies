"""Per-snippet JSONL trace of every agent step.

One file per (snippet, run) under ``<out_dir>/trajectories/<snippet>.jsonl``.
Each line records one event: ``llm_call``, ``tool_call``, ``build``, ``decision``.

Why JSONL: append-only, crash-safe (each line a complete record),
greppable, replayable. Required by G9 (reproducibility from day 1).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class TrajectoryLogger:
    def __init__(self, traj_dir: Path) -> None:
        self.traj_dir = Path(traj_dir)
        self.traj_dir.mkdir(parents=True, exist_ok=True)
        self._current: Path | None = None
        self._t0 = time.time()

    def start_snippet(self, snippet_id: str) -> None:
        self._current = self.traj_dir / f"{snippet_id}.jsonl"
        # Truncate prior content for clean replay; if you want incremental
        # append across resume, change to "a".
        self._current.write_text("", encoding="utf-8")
        self._t0 = time.time()
        self.log("snippet_start", {"id": snippet_id})

    def log(self, event: str, payload: dict[str, Any]) -> None:
        if self._current is None:
            return
        rec = {
            "t": round(time.time() - self._t0, 3),
            "event": event,
            **payload,
        }
        try:
            with self._current.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, default=str) + "\n")
        except OSError:
            pass

    # ----- typed helpers (keep call sites readable) ----------------------

    def log_llm(self, agent: str, prompt: str, response: str,
                tokens_approx: int = 0) -> None:
        self.log("llm_call", {
            "agent": agent,
            "prompt": prompt[:4000],   # truncate huge prompts for log readability
            "response": response[:4000],
            "tokens_approx": tokens_approx,
        })

    def log_tool(self, agent: str, tool: str, args: dict, result: Any) -> None:
        self.log("tool_call", {
            "agent": agent,
            "tool": tool,
            "args": args,
            "result": str(result)[:2000],
        })

    def log_build(self, py_ver: str, packages: list[str],
                  passed: bool, error_kind: str, duration: float) -> None:
        self.log("build", {
            "py_ver": py_ver,
            "packages": packages,
            "passed": passed,
            "error_kind": error_kind,
            "duration": round(duration, 3),
        })

    def log_decision(self, agent: str, decision: str, reason: str = "") -> None:
        self.log("decision", {"agent": agent, "decision": decision, "reason": reason})

    def end_snippet(self, passed: bool, n_steps: int) -> None:
        self.log("snippet_end", {"passed": passed, "n_steps": n_steps})
        self._current = None


def replay(jsonl_path: Path) -> list[dict]:
    """Load a trajectory back into memory for analysis / case sampling."""
    out: list[dict] = []
    if not jsonl_path.exists():
        return out
    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out

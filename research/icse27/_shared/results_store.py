"""Atomic results.csv writer with Ctrl-C-safe resume detection.

The existing MEMRES harness appends to results.csv non-atomically
(see tools/memres/run.py:318-327), so a Ctrl-C mid-write can corrupt
the CSV and lose all prior progress on long runs. This module fixes that.

Strategy
--------
1. On every snippet completion, rewrite the entire CSV to ``results.csv.tmp``
   then ``os.replace`` it onto ``results.csv``. POSIX-atomic; Windows-atomic
   on the same volume. Worst case on interrupt: the most recent snippet is
   missing — never a half-written file.
2. Resume scans the existing CSV at startup and returns the set of completed
   snippet IDs. The harness skips those when iterating the benchmark.
3. Heartbeat file (``heartbeat.json``) lets a second runner detect that a
   first runner is alive and refuse to start (prevents double-processing
   when a user accidentally launches two terminals).

This keeps the CSV schema compatible with existing tools/memres results
plus three new columns (seed, backbone, method) that the harness uses to
attribute each row.
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator

CSV_COLUMNS = (
    "name",            # snippet_id (matches existing schema)
    "file",            # output_data_X.Y.yml or "" if not written
    "result",          # error tag or "None" for pass
    "python_modules",  # semicolon-separated package names
    "duration",        # seconds (3 decimals)
    "passed",          # "True" or "False"
    # New columns for ICSE 2027 multi-method/multi-backbone runs
    "seed",
    "backbone",
    "method",
)


@dataclass
class ResultRow:
    name: str
    file: str = ""
    result: str = ""
    python_modules: str = ""
    duration: float = 0.0
    passed: bool = False
    seed: int = 0
    backbone: str = ""
    method: str = ""
    # Optional trajectory pointer (relative path under run dir); not persisted to CSV
    trajectory: str = field(default="", repr=False)

    def as_csv_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "file": self.file,
            "result": self.result,
            "python_modules": self.python_modules,
            "duration": f"{self.duration:.3f}",
            "passed": "True" if self.passed else "False",
            "seed": str(self.seed),
            "backbone": self.backbone,
            "method": self.method,
        }


class ResultsStore:
    """Owns a single run's results.csv. Not safe for concurrent processes."""

    def __init__(self, out_dir: Path, heartbeat_grace_sec: int = 120) -> None:
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.out_dir / "results.csv"
        self.heartbeat_path = self.out_dir / "heartbeat.json"
        self.heartbeat_grace_sec = heartbeat_grace_sec
        self._rows: list[ResultRow] = self._load_existing()

    # ----- resume detection -----------------------------------------------

    def _load_existing(self) -> list[ResultRow]:
        if not self.csv_path.exists():
            return []
        out: list[ResultRow] = []
        with self.csv_path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    out.append(
                        ResultRow(
                            name=row["name"],
                            file=row.get("file", ""),
                            result=row.get("result", ""),
                            python_modules=row.get("python_modules", ""),
                            duration=float(row.get("duration", "0") or 0),
                            passed=row.get("passed", "False").strip().lower() == "true",
                            seed=int(row.get("seed", "0") or 0),
                            backbone=row.get("backbone", ""),
                            method=row.get("method", ""),
                        )
                    )
                except (KeyError, ValueError):
                    # Skip corrupt rows rather than aborting — surface count later.
                    continue
        return out

    def completed_ids(self) -> set[str]:
        """Snippet IDs already in the CSV — harness skips these on resume."""
        return {r.name for r in self._rows}

    def num_rows(self) -> int:
        return len(self._rows)

    # ----- atomic append --------------------------------------------------

    def append(self, row: ResultRow) -> None:
        """Add one row and atomically rewrite results.csv."""
        self._rows.append(row)
        self._atomic_rewrite()

    def _atomic_rewrite(self) -> None:
        fd, tmp_path = tempfile.mkstemp(
            prefix="results.csv.", suffix=".tmp", dir=str(self.out_dir)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                for r in self._rows:
                    writer.writerow(r.as_csv_dict())
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.csv_path)
        except Exception:
            # Don't leave stale .tmp around if rewrite failed.
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    # ----- heartbeat ------------------------------------------------------

    def claim_run_or_raise(self) -> None:
        """Refuse to start if another runner is alive in the same out_dir.

        ``heartbeat.json`` carries the pid, start_time, and last_update.
        If the last update is fresh (< grace_sec), assume a runner is live.
        Stale heartbeats are silently reclaimed.
        """
        if self.heartbeat_path.exists():
            try:
                data = json.loads(self.heartbeat_path.read_text(encoding="utf-8"))
                last_update = float(data.get("last_update", 0))
                if time.time() - last_update < self.heartbeat_grace_sec:
                    raise RuntimeError(
                        f"Another runner appears active in {self.out_dir} "
                        f"(pid={data.get('pid')}, last update "
                        f"{time.time() - last_update:.0f}s ago). "
                        f"Delete {self.heartbeat_path} if this is stale."
                    )
            except (json.JSONDecodeError, OSError, ValueError):
                pass  # corrupt heartbeat → treat as stale
        self._write_heartbeat(current_snippet="")

    def _write_heartbeat(self, current_snippet: str) -> None:
        payload = {
            "pid": os.getpid(),
            "start_time": getattr(self, "_start_time", time.time()),
            "last_update": time.time(),
            "current_snippet": current_snippet,
            "rows_so_far": len(self._rows),
        }
        if not hasattr(self, "_start_time"):
            self._start_time = payload["start_time"]
        # Heartbeat writes are best-effort; corruption here doesn't lose data.
        try:
            self.heartbeat_path.write_text(json.dumps(payload), encoding="utf-8")
        except OSError:
            pass

    @contextmanager
    def processing(self, snippet_id: str) -> Iterator[None]:
        """Heartbeat the currently-processed snippet."""
        self._write_heartbeat(snippet_id)
        try:
            yield
        finally:
            self._write_heartbeat("")

    def release(self) -> None:
        """Remove heartbeat on clean shutdown."""
        try:
            self.heartbeat_path.unlink()
        except OSError:
            pass

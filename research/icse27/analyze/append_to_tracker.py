"""Append a finished run as one row in tracker.md.

Reads ``<run_dir>/results.csv`` and ``run.json``, computes pass rate +
mean duration, and inserts a row before the ``## Insights`` section
of ``research/icse27/tracker.md``. Idempotent: the run dir is the key,
so re-running won't duplicate a row.

Usage:
    python -m research.icse27.analyze.append_to_tracker \\
        --run results/icse27/m4_cgar_multiagent/gemma2-9b/hg2k_smoke/seed0 \\
        [--note "first multi-agent run; debate disabled"]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from research.icse27._shared import ICSE27_DIR, PROJECT_ROOT


def _summary(run_dir: Path) -> dict:
    csv_path = run_dir / "results.csv"
    meta_path = run_dir / "run.json"
    n = passed = 0
    total_dur = 0.0
    if csv_path.exists():
        with csv_path.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                n += 1
                raw = (r.get("passed", "False") or "False").strip().lower()
                if raw == "true" or (raw.isdigit() and int(raw) > 0):
                    passed += 1
                try:
                    total_dur += float(r.get("duration", "0") or 0)
                except ValueError:
                    pass
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return {
        "method": meta.get("method", "?"),
        "backbone": meta.get("backbone", "?"),
        "benchmark": meta.get("benchmark", "?"),
        "seed": meta.get("seed", "?"),
        "n": n, "passed": passed,
        "mean_dur": (total_dur / n) if n else 0.0,
    }


def main(argv: list[str] | None = None) -> int:
    import datetime as _dt

    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path, help="Run directory")
    ap.add_argument("--note", default="")
    args = ap.parse_args(argv)

    run_dir_abs = args.run.resolve()
    try:
        rel = run_dir_abs.relative_to(PROJECT_ROOT)
    except ValueError:
        rel = run_dir_abs
    s = _summary(run_dir_abs)
    today = _dt.date.today().isoformat()

    tracker = ICSE27_DIR / "tracker.md"
    text = tracker.read_text(encoding="utf-8")

    if str(rel) in text:
        print(f"Run already in tracker: {rel}; skipping")
        return 0

    # NOTE: no DOTALL flag. Match line-by-line via [^\n]* so the body capture
    # stops at the first non-pipe line (the blank line after the table).
    table_re = re.compile(r"(\| # \| Date \| Run dir \|[^\n]*\n\|---[^\n]*\n)((?:\|[^\n]*\n)*)")
    m = table_re.search(text)
    if not m:
        print("Could not locate tracker table; aborting", file=sys.stderr)
        return 2
    header, body = m.group(1), m.group(2)
    existing_rows = [r for r in body.splitlines() if r.startswith("|")]
    next_idx = len(existing_rows) + 1
    pass_rate = (s["passed"] / s["n"] * 100) if s["n"] else 0.0
    new_row = (
        f"| {next_idx} | {today} | `{rel}` | {s['method']} | {s['backbone']} | "
        f"{s['benchmark']} | {s['seed']} | {s['passed']}/{s['n']} "
        f"({pass_rate:.1f}%) | {s['mean_dur']:.1f}s | {args.note} |\n"
    )
    new_body = body + new_row
    text = text[:m.start()] + header + new_body + text[m.end():]
    tracker.write_text(text, encoding="utf-8")
    print(f"appended row #{next_idx}: {s['passed']}/{s['n']} ({pass_rate:.1f}%) {args.note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

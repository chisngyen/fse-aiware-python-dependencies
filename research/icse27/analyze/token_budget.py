"""Report LLM token usage per method (G6 + G8).

Reads ``llm_usage.json`` (written by run_experiment) and produces a
compact Markdown report. Use this to detect when a new method's cost
balloons relative to its accuracy delta.

Usage:
    python -m research.icse27.analyze.token_budget --runs path/to/m4 path/to/m5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load(run_dir: Path) -> dict:
    usage = run_dir / "llm_usage.json"
    meta = run_dir / "run.json"
    out: dict = {"run": str(run_dir)}
    if usage.exists():
        out.update(json.loads(usage.read_text(encoding="utf-8")))
    if meta.exists():
        m = json.loads(meta.read_text(encoding="utf-8"))
        out["method"] = m.get("method", "")
        out["backbone"] = m.get("backbone", "")
        out["n_processed"] = m.get("n_processed", 0)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", type=Path, required=True)
    args = ap.parse_args(argv)

    rows = [_load(p) for p in args.runs]
    print("| Method | Backbone | n | LLM calls | calls/snip | prompt_chars | resp_chars | LLM wall (s) | LLM err |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        n = r.get("n_processed", 0) or 0
        calls = r.get("calls", 0)
        cps = (calls / n) if n else 0
        print(f"| {r.get('method','—')} | {r.get('backbone','—')} | {n} | "
              f"{calls} | {cps:.2f} | {r.get('prompt_chars',0)} | "
              f"{r.get('response_chars',0)} | {r.get('total_wall_sec',0):.1f} | "
              f"{r.get('errors',0)} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())

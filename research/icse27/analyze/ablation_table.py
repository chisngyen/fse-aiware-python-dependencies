"""Auto-build an ablation table from multiple methods' results.csv files (G5).

Each row = one method. Cols = pass rate, mean duration, n. Output is
Markdown (paste-into-tracker) and optionally LaTeX.

Usage:
    python -m research.icse27.analyze.ablation_table \\
        --csvs path/to/m3/results.csv path/to/m4/results.csv path/to/m5/results.csv \\
        [--format md|latex]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def _summary(path: Path) -> dict:
    n = passed = 0
    total_dur = 0.0
    method = backbone = ""
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            n += 1
            raw = (r.get("passed", "False") or "False").strip().lower()
            if raw == "true" or (raw.isdigit() and int(raw) > 0):
                passed += 1
            try:
                total_dur += float(r.get("duration", "0") or 0)
            except ValueError:
                pass
            method = r.get("method", method)
            backbone = r.get("backbone", backbone)
    return {
        "path": str(path),
        "method": method or path.parent.parent.name,
        "backbone": backbone,
        "n": n,
        "pass_rate": (passed / n) if n else 0.0,
        "mean_dur": (total_dur / n) if n else 0.0,
    }


def render_md(rows: list[dict]) -> str:
    lines = [
        "| Method | Backbone | n | Pass rate | Mean dur (s) |",
        "|---|---|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['method']} | {r['backbone'] or '—'} | {r['n']} | "
            f"{r['pass_rate']*100:.1f}% | {r['mean_dur']:.1f} |"
        )
    return "\n".join(lines)


def render_latex(rows: list[dict]) -> str:
    out = ["\\begin{tabular}{l l r r r}",
           "\\toprule",
           "Method & Backbone & $n$ & Pass rate & Mean dur (s) \\\\",
           "\\midrule"]
    for r in rows:
        out.append(f"{r['method']} & {r['backbone'] or '-'} & {r['n']} & "
                   f"{r['pass_rate']*100:.1f}\\% & {r['mean_dur']:.1f} \\\\")
    out += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csvs", nargs="+", type=Path, required=True)
    ap.add_argument("--format", choices=("md", "latex"), default="md")
    args = ap.parse_args(argv)
    rows = [_summary(p) for p in args.csvs]
    print(render_md(rows) if args.format == "md" else render_latex(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())

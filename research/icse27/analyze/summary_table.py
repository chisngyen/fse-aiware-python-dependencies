"""Summary table — one row per (method, backbone, benchmark, seed).

Scans ``results/icse27/`` and prints a Markdown table of every completed
run. Use this as the "what have I run?" overview before paper writing.

Usage:
    python -m research.icse27.analyze.summary_table              # everything
    python -m research.icse27.analyze.summary_table --benchmark hg2k_full
    python -m research.icse27.analyze.summary_table --markdown   # paper-ready md
    python -m research.icse27.analyze.summary_table --csv        # tsv export
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from research.icse27._shared import DEFAULT_RESULTS_DIR


def _summarize_one(run_dir: Path) -> dict | None:
    csv_path = run_dir / "results.csv"
    if not csv_path.exists():
        return None
    rows = []
    try:
        with csv_path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    except OSError:
        return None
    if not rows:
        return None
    n = len(rows)
    passed = 0
    total_dur = 0.0
    for r in rows:
        raw = (r.get("passed", "False") or "False").strip().lower()
        if raw == "true" or (raw.isdigit() and int(raw) > 0):
            passed += 1
        try:
            total_dur += float(r.get("duration", "0") or 0)
        except ValueError:
            pass
    # Path: results/icse27/<method>/<backbone>/<benchmark>/seed<N>
    parts = run_dir.parts
    try:
        idx = parts.index("icse27")
        method = parts[idx + 1]
        backbone = parts[idx + 2]
        benchmark = parts[idx + 3]
        seed = parts[idx + 4]
    except (ValueError, IndexError):
        method = backbone = benchmark = seed = "?"
    # Heartbeat = still running
    hb = run_dir / "heartbeat.json"
    running = False
    if hb.exists():
        try:
            import time
            data = json.loads(hb.read_text(encoding="utf-8"))
            running = (time.time() - float(data.get("last_update", 0))) < 60
        except (json.JSONDecodeError, ValueError, OSError):
            pass
    return {
        "method": method,
        "backbone": backbone,
        "benchmark": benchmark,
        "seed": seed,
        "n": n,
        "passed": passed,
        "pass_rate": passed / n,
        "mean_dur": total_dur / n,
        "running": running,
        "path": str(run_dir),
    }


def scan(root: Path) -> list[dict]:
    out: list[dict] = []
    if not root.exists():
        return out
    for results_csv in sorted(root.rglob("results.csv")):
        s = _summarize_one(results_csv.parent)
        if s is not None:
            out.append(s)
    return out


def render_markdown(rows: list[dict]) -> str:
    if not rows:
        return "_No runs found._"
    # Group by benchmark for clarity
    benchmarks = sorted({r["benchmark"] for r in rows})
    lines: list[str] = []
    for bench in benchmarks:
        lines.append(f"\n### Benchmark: `{bench}`\n")
        lines.append("| Method | Backbone | Seed | n | Pass | Pass rate | Mean dur (s) | Status |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---|")
        bench_rows = sorted([r for r in rows if r["benchmark"] == bench],
                            key=lambda r: (r["method"], r["backbone"], r["seed"]))
        for r in bench_rows:
            status = "running" if r["running"] else "done"
            lines.append(
                f"| {r['method']} | {r['backbone']} | {r['seed']} | "
                f"{r['n']} | {r['passed']} | {r['pass_rate']*100:.1f}% | "
                f"{r['mean_dur']:.1f} | {status} |"
            )
    return "\n".join(lines)


def render_tsv(rows: list[dict]) -> str:
    out = ["method\tbackbone\tbenchmark\tseed\tn\tpassed\tpass_rate\tmean_dur\trunning"]
    for r in rows:
        out.append("\t".join([
            r["method"], r["backbone"], r["benchmark"], r["seed"],
            str(r["n"]), str(r["passed"]), f"{r['pass_rate']*100:.2f}",
            f"{r['mean_dur']:.2f}", str(r["running"]),
        ]))
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=DEFAULT_RESULTS_DIR,
                    help="Root directory to scan (default: results/icse27)")
    ap.add_argument("--benchmark", default=None,
                    help="Filter to a specific benchmark")
    ap.add_argument("--method", default=None,
                    help="Filter to method name substring")
    ap.add_argument("--csv", action="store_true",
                    help="Output TSV (tab-separated) instead of Markdown")
    ap.add_argument("--markdown", action="store_true",
                    help="Output Markdown (default)")
    args = ap.parse_args(argv)

    rows = scan(args.root)
    if args.benchmark:
        rows = [r for r in rows if r["benchmark"] == args.benchmark]
    if args.method:
        rows = [r for r in rows if args.method in r["method"]]

    if not rows:
        print("No runs found under", args.root, file=sys.stderr)
        return 1

    if args.csv:
        print(render_tsv(rows))
    else:
        print(render_markdown(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())

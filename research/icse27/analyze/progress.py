"""Live progress watcher for a running experiment.

Run in a separate terminal alongside ``run_experiment``. Re-reads
``results.csv`` + ``heartbeat.json`` every N seconds and prints:
  - snippets done / total (inferred from ids_file)
  - pass rate so far
  - mean / max duration so far
  - ETA based on mean duration × remaining
  - currently-processed snippet from heartbeat

Usage:
    python -m research.icse27.analyze.progress \\
        --run results/icse27/m4_neurosymbolic_temporal/gemma2-9b/hg2k_smoke/seed0 \\
        [--every 10]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

from research.icse27._shared import CONFIGS_DIR, load_tier_ids


def _read_csv(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _passed(r: dict) -> bool:
    raw = (r.get("passed", "False") or "False").strip().lower()
    return raw == "true" or (raw.isdigit() and int(raw) > 0)


def _total_from_meta(run_dir: Path) -> int | None:
    """Try to infer dataset size from run.json + benchmark config."""
    meta_p = run_dir / "run.json"
    if not meta_p.exists():
        return None
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    bench_name = meta.get("benchmark", "")
    if not bench_name:
        return None
    import yaml
    cfg_p = CONFIGS_DIR / "benchmarks" / f"{bench_name}.yaml"
    if not cfg_p.exists():
        return None
    cfg = yaml.safe_load(cfg_p.read_text(encoding="utf-8"))
    ids_file = cfg.get("ids_file") or ""
    if ids_file:
        ids = load_tier_ids(CONFIGS_DIR / "benchmarks" / ids_file)
        return len(ids) if ids else None
    return None


def _fmt_sec(s: float) -> str:
    if s < 60: return f"{s:.0f}s"
    if s < 3600: return f"{s/60:.1f}m"
    return f"{s/3600:.1f}h"


def render(run_dir: Path, total: int | None) -> str:
    rows = _read_csv(run_dir / "results.csv")
    n = len(rows)
    passed = sum(1 for r in rows if _passed(r))
    durs = []
    for r in rows:
        try:
            durs.append(float(r.get("duration", 0) or 0))
        except ValueError:
            pass
    mean_dur = (sum(durs) / len(durs)) if durs else 0.0
    max_dur = max(durs) if durs else 0.0

    hb_p = run_dir / "heartbeat.json"
    cur = "(no heartbeat)"
    age = "?"
    if hb_p.exists():
        try:
            hb = json.loads(hb_p.read_text(encoding="utf-8"))
            cur = hb.get("current_snippet", "") or "(idle)"
            age = _fmt_sec(time.time() - float(hb.get("last_update", 0)))
        except (json.JSONDecodeError, ValueError):
            pass

    pct = (n / total * 100) if total else 0
    remaining = (total - n) if total else 0
    eta = _fmt_sec(remaining * mean_dur) if remaining and mean_dur else "?"
    pass_rate = (passed / n * 100) if n else 0

    return (
        f"[{n}/{total or '?'}] {pct:5.1f}% | "
        f"pass {passed}/{n} ({pass_rate:.1f}%) | "
        f"avg {mean_dur:.0f}s max {max_dur:.0f}s | "
        f"ETA {eta} | "
        f"now: {cur[:12]} (hb {age} ago)"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--every", type=int, default=10,
                    help="Refresh interval in seconds")
    ap.add_argument("--once", action="store_true",
                    help="Print one snapshot and exit (no loop)")
    args = ap.parse_args(argv)

    if not args.run.exists():
        print(f"Run dir does not exist: {args.run}", file=sys.stderr)
        return 1

    total = _total_from_meta(args.run)
    if args.once:
        print(render(args.run, total))
        return 0

    try:
        while True:
            line = render(args.run, total)
            print(f"\r{line}   ", end="", flush=True)
            time.sleep(args.every)
    except KeyboardInterrupt:
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())

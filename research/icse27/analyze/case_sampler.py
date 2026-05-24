"""Uniform case sampler — enforces G4 (no cherry-picking).

Given a "new" results.csv and a "baseline" results.csv, samples:
- 5 wins (new pass, baseline fail)
- 5 both-pass (sanity: new isn't slower for free)
- 5 losses (new fail, baseline pass — honest failure analysis)

Outputs a Markdown gallery with snippet code excerpts + trajectory pointers.

Usage:
    python -m research.icse27.analyze.case_sampler \\
        --new path/to/m4/results.csv --baseline path/to/m2/results.csv \\
        --traj-new path/to/m4/trajectories \\
        --out cases.md
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

from research.icse27._shared import HARD_GISTS_DIR, GITCHAMELEON_DIR


def _load(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return {r["name"]: r for r in csv.DictReader(f) if r.get("name")}


def _pass(row: dict) -> bool:
    raw = (row.get("passed", "False") or "False").strip().lower()
    return raw == "true" or (raw.isdigit() and int(raw) > 0)


def _snippet_path(sid: str) -> Path | None:
    for root in (HARD_GISTS_DIR, GITCHAMELEON_DIR):
        p = root / sid / "snippet.py"
        if p.exists():
            return p
    return None


def _section(title: str, ids: list[str], new: dict, base: dict, traj_dir: Path | None) -> str:
    lines = [f"## {title} (n={len(ids)})", ""]
    for sid in ids:
        n_row = new[sid]
        b_row = base.get(sid, {})
        path = _snippet_path(sid)
        lines.append(f"### `{sid}`")
        lines.append(f"- new: passed={_pass(n_row)}  duration={n_row.get('duration')}  result={n_row.get('result')}")
        lines.append(f"- base: passed={_pass(b_row)}  duration={b_row.get('duration')}  result={b_row.get('result')}")
        if path:
            src = path.read_text(encoding="utf-8", errors="replace")[:600]
            lines.append("```python")
            lines.append(src)
            lines.append("```")
        if traj_dir is not None and (traj_dir / f"{sid}.jsonl").exists():
            lines.append(f"- trajectory: `{traj_dir / f'{sid}.jsonl'}`")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", required=True, type=Path)
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--traj-new", type=Path, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("cases.md"))
    ap.add_argument("--k", type=int, default=5, help="cases per bucket")
    args = ap.parse_args(argv)

    new, base = _load(args.new), _load(args.baseline)
    shared = sorted(set(new) & set(base))
    wins = [s for s in shared if _pass(new[s]) and not _pass(base[s])]
    losses = [s for s in shared if not _pass(new[s]) and _pass(base[s])]
    both_pass = [s for s in shared if _pass(new[s]) and _pass(base[s])]

    rng = random.Random(args.seed)
    rng.shuffle(wins)
    rng.shuffle(losses)
    rng.shuffle(both_pass)

    md = "\n".join([
        f"# Case gallery — uniformly sampled (seed={args.seed})",
        "",
        f"- shared snippets: {len(shared)}",
        f"- wins (new>baseline): {len(wins)}  / losses (new<baseline): {len(losses)}  / both-pass: {len(both_pass)}",
        "",
        _section("Wins (new passes, baseline fails)", wins[:args.k], new, base, args.traj_new),
        _section("Both pass (efficiency sanity check)", both_pass[:args.k], new, base, args.traj_new),
        _section("Losses (new fails, baseline passes — honest failure analysis)",
                 losses[:args.k], new, base, args.traj_new),
    ])
    args.out.write_text(md, encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Paired comparison between two methods' results.csv (G6).

Reports:
- Pass rate delta + bootstrap 95% CI on the delta
- Wilcoxon signed-rank p-value on per-snippet pass/fail and on duration
- Wins / losses / ties counts

Usage:
    python -m research.icse27.analyze.pairwise_stats \\
        --a path/to/m4/results.csv --b path/to/m2/results.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path


def _load(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return {r["name"]: r for r in csv.DictReader(f) if r.get("name")}


def _pass(row: dict) -> int:
    raw = (row.get("passed", "False") or "False").strip().lower()
    if raw == "true":
        return 1
    if raw.isdigit():
        return 1 if int(raw) > 0 else 0
    return 0


def _duration(row: dict) -> float:
    try:
        return float(row.get("duration", "0") or 0)
    except ValueError:
        return 0.0


def _bootstrap_ci(diffs: list[int], n_boot: int = 5000, seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(diffs)
    if n == 0:
        return (0.0, 0.0)
    means: list[float] = []
    for _ in range(n_boot):
        means.append(sum(rng.choice(diffs) for _ in range(n)) / n)
    means.sort()
    lo = means[int(0.025 * n_boot)]
    hi = means[int(0.975 * n_boot)]
    return (lo, hi)


def _wilcoxon(diffs: list[float]) -> float:
    """SciPy if available; otherwise normal-approx z-test on signed ranks."""
    nonzero = [d for d in diffs if d != 0]
    if not nonzero:
        return 1.0
    try:
        from scipy.stats import wilcoxon  # type: ignore
        return float(wilcoxon(nonzero).pvalue)
    except ImportError:
        ranks = sorted(range(len(nonzero)), key=lambda i: abs(nonzero[i]))
        # very rough fallback — discourages relying on this without scipy
        signed = sum((r + 1) if nonzero[i] > 0 else -(r + 1)
                     for r, i in enumerate(ranks))
        return min(1.0, abs(signed) / (sum(r + 1 for r in range(len(nonzero))) or 1))


def report(a_csv: Path, b_csv: Path) -> dict:
    a, b = _load(a_csv), _load(b_csv)
    shared = sorted(set(a) & set(b))
    if not shared:
        raise ValueError("No shared snippet IDs between the two result files")
    pass_diff = [_pass(a[s]) - _pass(b[s]) for s in shared]
    dur_diff = [_duration(a[s]) - _duration(b[s]) for s in shared]
    wins = sum(1 for d in pass_diff if d > 0)
    losses = sum(1 for d in pass_diff if d < 0)
    ties = sum(1 for d in pass_diff if d == 0)
    a_rate = sum(_pass(a[s]) for s in shared) / len(shared)
    b_rate = sum(_pass(b[s]) for s in shared) / len(shared)
    ci_lo, ci_hi = _bootstrap_ci(pass_diff)
    return {
        "n": len(shared),
        "a_pass_rate": a_rate,
        "b_pass_rate": b_rate,
        "delta": a_rate - b_rate,
        "delta_ci95": (ci_lo, ci_hi),
        "wins_a_over_b": wins,
        "losses_a_under_b": losses,
        "ties": ties,
        "wilcoxon_p_pass": _wilcoxon([float(d) for d in pass_diff]),
        "wilcoxon_p_duration": _wilcoxon(dur_diff),
        "mean_duration_a": sum(_duration(a[s]) for s in shared) / len(shared),
        "mean_duration_b": sum(_duration(b[s]) for s in shared) / len(shared),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, type=Path)
    ap.add_argument("--b", required=True, type=Path)
    args = ap.parse_args(argv)
    rep = report(args.a, args.b)
    print(f"n shared snippets : {rep['n']}")
    print(f"A pass rate        : {rep['a_pass_rate']:.4f}")
    print(f"B pass rate        : {rep['b_pass_rate']:.4f}")
    print(f"delta (A - B)      : {rep['delta']:+.4f}  95% CI {rep['delta_ci95']}")
    print(f"wins/losses/ties   : {rep['wins_a_over_b']}/{rep['losses_a_under_b']}/{rep['ties']}")
    print(f"Wilcoxon p (pass)  : {rep['wilcoxon_p_pass']:.4g}")
    print(f"Wilcoxon p (dur)   : {rep['wilcoxon_p_duration']:.4g}")
    print(f"mean dur A / B (s) : {rep['mean_duration_a']:.2f} / {rep['mean_duration_b']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

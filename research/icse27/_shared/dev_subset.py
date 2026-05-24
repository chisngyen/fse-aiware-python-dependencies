"""Stratified subset sampler — turns a 1-day run into a 30-min/3-hr iteration loop.

Tiers (HG2.9K, the primary benchmark per user requirement)
----------------------------------------------------------
- ``smoke`` (n=50)    ~30 min  — validate a code change doesn't break the pipeline
- ``dev`` (n=300)     ~3-4 hr  — A/B compare methods during iteration
- ``rescue`` (n=494)  ~3 hr    — MEMRES-failure cases, targeted improvement signal
- ``full`` (n=2891)   ~1 day   — paper headline numbers only

Stratification key
------------------
We stratify by **PLLM result type** (SyntaxError / NoMatchingDistribution /
ImportError / Other / Pass) using existing ``results/hg2k/pllm/results.csv``.
This guarantees the subset covers all the error families that motivate
each agentic mechanism (Archaeologist solves Python era, Doctor solves
ImportError, etc.).

Subsets are deterministic: same seed → same snippet IDs.
The ID list is materialized to a file under
``research/icse27/configs/benchmarks/<tier>.ids.txt`` so that every
method/seed/backbone in the dev tier sees IDENTICAL snippets (G3 parity).
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

from .paths import PROJECT_ROOT, CONFIGS_DIR

PLLM_HG2K_CSV = PROJECT_ROOT / "results" / "hg2k" / "pllm" / "csv" / "summary-all-runs.csv"
MEMRES_HG2K_CSV = PROJECT_ROOT / "results" / "hg2k" / "memres" / "run_1" / "results.csv"

TIER_SIZES = {
    # The two ICSE 2027 benchmarks modes (per user spec 2026-05-24):
    "20pct": None,      # ~20% of full (stratified) — quick eval mode
    "full": None,       # whole benchmark — paper headline mode
    # Historical (kept for back-compat, not active):
    "smoke": 50,
    "dev": 300,
    "rescue": None,
}


def _read_results(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        return []
    with csv_path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _stratify_by_result(rows: list[dict[str, str]]) -> dict[str, list[str]]:
    """Group snippet IDs by their PLLM result family.

    Families collapse the long tail of ad-hoc error tags into 6 buckets:
    Pass / SyntaxError / NoMatchDist / ImportError / NoWheel / Other.
    """
    buckets: dict[str, list[str]] = {k: [] for k in
        ("Pass", "SyntaxError", "NoMatchDist", "ImportError", "NoWheel", "Other")}
    for r in rows:
        name = r.get("name", "")
        # Accept both bool ("True"/"False") and count-of-runs ("10"/"0") formats.
        raw = (r.get("passed", "False") or "False").strip().lower()
        passed = raw == "true" or (raw.isdigit() and int(raw) > 0)
        result = (r.get("result") or "").strip()
        if passed:
            key = "Pass"
        elif "SyntaxError" in result:
            key = "SyntaxError"
        elif "NoMatching" in result or "NoMatchDist" in result:
            key = "NoMatchDist"
        elif "ImportError" in result or "ModuleNotFound" in result:
            key = "ImportError"
        elif "Wheel" in result:
            key = "NoWheel"
        else:
            key = "Other"
        if name:
            buckets[key].append(name)
    return buckets


def build_subset(tier: str, seed: int = 0) -> list[str]:
    """Return sorted list of snippet IDs for the requested tier."""
    pllm_rows = _read_results(PLLM_HG2K_CSV)

    if tier == "full":
        return sorted(r["name"] for r in pllm_rows if r.get("name"))

    if tier == "rescue":
        memres_rows = _read_results(MEMRES_HG2K_CSV)
        return sorted(r["name"] for r in memres_rows
                      if r.get("name") and r.get("passed", "False").strip().lower() != "true")

    # 20% mode: stratified ~20% of full benchmark (preserves error-family distribution)
    if tier == "20pct":
        size = max(1, len(pllm_rows) // 5)
    else:
        size = TIER_SIZES.get(tier)
    if size is None:
        raise ValueError(f"Unknown tier {tier!r}")

    buckets = _stratify_by_result(pllm_rows)
    # Proportional allocation, with floor=2 per non-empty bucket so every
    # error family is represented even in the smoke tier.
    total = sum(len(v) for v in buckets.values()) or 1
    raw_alloc = {k: max(2, round(size * len(v) / total)) if v else 0
                 for k, v in buckets.items()}
    # Trim to exact size deterministically (sorted by bucket name).
    keys = sorted(raw_alloc.keys())
    while sum(raw_alloc.values()) > size:
        # shave from the largest bucket first
        k = max(keys, key=lambda x: raw_alloc[x])
        if raw_alloc[k] > 2:
            raw_alloc[k] -= 1
        else:
            break
    while sum(raw_alloc.values()) < size:
        k = max(keys, key=lambda x: len(buckets[x]) - raw_alloc[x])
        raw_alloc[k] += 1

    rng = random.Random(seed)
    out: list[str] = []
    for k in keys:
        pool = sorted(buckets[k])  # deterministic input
        rng.shuffle(pool)
        out.extend(pool[: raw_alloc[k]])
    return sorted(out)


def materialize_tier(tier: str, seed: int = 0) -> Path:
    """Write tier ID list to configs/benchmarks/hg2k_<tier>.ids.txt and return path."""
    ids = build_subset(tier, seed=seed)
    out_dir = CONFIGS_DIR / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"hg2k_{tier}.ids.txt"
    out_path.write_text("\n".join(ids) + "\n", encoding="utf-8")
    return out_path


def load_tier_ids(tier_file: Path) -> set[str]:
    """Read materialized tier file; returns set for O(1) membership in iter_snippets filter."""
    if not tier_file.exists():
        return set()
    return {ln.strip() for ln in tier_file.read_text(encoding="utf-8").splitlines() if ln.strip()}

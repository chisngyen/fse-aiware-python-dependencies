"""Canonical absolute paths used across the experimental harness.

Resolved once at import time so every module agrees on where things live,
regardless of the current working directory the user invokes from.
"""

from pathlib import Path

# research/icse27/_shared/paths.py → repo root = parents[3]
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Datasets (read-only, ground truth not shown to methods)
HARD_GISTS_DIR = PROJECT_ROOT / "benchmarks" / "hard-gists"
GITCHAMELEON_DIR = PROJECT_ROOT / "benchmarks" / "gitchameleon-snippets"
GITCHAMELEON_GT_CSV = GITCHAMELEON_DIR / "ground_truth.csv"

# Frozen baseline tools (referenced by replay methods; never modified)
TOOLS_DIR = PROJECT_ROOT / "tools"
MEMRES_DIR = TOOLS_DIR / "memres"
CGAR_DIR = TOOLS_DIR / "cgar"
PLLM_DIR = TOOLS_DIR / "pllm"

# Experiment workspace (this package's home)
ICSE27_DIR = PROJECT_ROOT / "research" / "icse27"
METHODS_DIR = ICSE27_DIR / "methods"
CONFIGS_DIR = ICSE27_DIR / "configs"

# Default output location for runs (each run gets a subfolder under here)
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results" / "icse27"


def assert_layout_ok() -> None:
    """Fail loud (G12) if the repo layout doesn't match expectations."""
    missing = [p for p in (HARD_GISTS_DIR, GITCHAMELEON_DIR, MEMRES_DIR, CGAR_DIR) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "ICSE27 harness expects these paths to exist:\n  "
            + "\n  ".join(str(m) for m in missing)
            + f"\nPROJECT_ROOT resolved to: {PROJECT_ROOT}"
        )

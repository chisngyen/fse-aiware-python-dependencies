"""Unified dataset loader for HG2.9K and GitChameleon.

Methods only see (snippet_id, source_code, expected_python_hint).
Ground truth (when it exists) is loaded separately and never passed
to the method — it's only used for offline analysis. This enforces
G7 (no leakage): the method must discover versions purely from imports.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .paths import GITCHAMELEON_DIR, GITCHAMELEON_GT_CSV, HARD_GISTS_DIR

BENCHMARK_NAMES = ("hg2k", "gitchameleon")


@dataclass(frozen=True)
class Snippet:
    """Minimal contract that every method receives.

    - ``id``: stable identifier used as the primary key in results.csv
              (gist hash for HG2.9K, "sample_N" for GitChameleon).
    - ``path``: absolute path to snippet.py on disk.
    - ``source``: full Python source as text.
    - ``benchmark``: which benchmark the snippet came from.
    - ``hint_python``: optional hint of Python major.minor from the
            dataset's filename (e.g. "3.6" for GitChameleon). Methods
            MAY use this as a prior; baselines may ignore it. Never
            contains pinned package versions — those are ground truth.
    """

    id: str
    path: Path
    source: str
    benchmark: str
    hint_python: str | None = None

    @property
    def short_id(self) -> str:
        """First 8 chars — for log readability only."""
        return self.id[:8]


def _hint_python_from_yml(snippet_dir: Path) -> str | None:
    """Extract Python major.minor from output_data_X.Y.yml filename if present.

    For GitChameleon every sample has it; for HG2.9K only snippets that
    already have a PLLM/MEMRES result will. We expose this as a hint only.
    """
    for f in snippet_dir.iterdir():
        name = f.name
        if name.startswith("output_data_") and name.endswith(".yml"):
            # output_data_3.6.yml → "3.6"
            return name[len("output_data_") : -len(".yml")]
    return None


def iter_snippets(benchmark: str, limit: int | None = None) -> Iterator[Snippet]:
    """Yield snippets in deterministic order for resume safety.

    Sort by directory name (lexicographic) so the iteration order is
    stable across machines and reruns. Resume detection in
    ``results_store`` relies on this ordering being the same on restart.
    """
    if benchmark == "hg2k":
        root = HARD_GISTS_DIR
    elif benchmark == "gitchameleon":
        root = GITCHAMELEON_DIR
    else:
        raise ValueError(f"Unknown benchmark: {benchmark!r}. Known: {BENCHMARK_NAMES}")

    dirs = sorted(d for d in root.iterdir() if d.is_dir())
    n = 0
    for d in dirs:
        snippet_py = d / "snippet.py"
        if not snippet_py.exists():
            continue  # skip non-snippet folders (e.g. metadata)
        try:
            source = snippet_py.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        yield Snippet(
            id=d.name,
            path=snippet_py,
            source=source,
            benchmark=benchmark,
            hint_python=_hint_python_from_yml(d),
        )
        n += 1
        if limit is not None and n >= limit:
            return


def load_ground_truth(benchmark: str) -> dict[str, dict[str, str]]:
    """Load ground-truth versions for offline analysis. NEVER pass to methods.

    Returns {snippet_id: {package: version}} for GitChameleon.
    HG2.9K has no canonical ground truth so we return {}.
    """
    if benchmark == "gitchameleon":
        if not GITCHAMELEON_GT_CSV.exists():
            return {}
        gt: dict[str, dict[str, str]] = {}
        with GITCHAMELEON_GT_CSV.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("sample_id") or row.get("id") or row.get("name")
                if not sid:
                    continue
                pkg = row.get("package") or row.get("library")
                ver = row.get("version") or row.get("ground_truth_version")
                if not pkg or not ver:
                    continue
                gt.setdefault(sid, {})[pkg] = ver
        return gt
    return {}

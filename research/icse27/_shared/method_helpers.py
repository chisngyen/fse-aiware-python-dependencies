"""Shared helpers for method files (m7, m10, m11, m12, m13, m14).

These were duplicated across ~30% of each method file (~150 LOC × 5 files
= 750 LOC of pure boilerplate). Extracted here so each method file
focuses on its *unique mechanism*, not on loading CSVs and parsing JSON.

Imports stay minimal: methods do
    from research.icse27._shared.method_helpers import (
        looks_like_python2, STDLIB, load_resolver_csv,
        passed, packages_of, py_of, cascade_replay,
        parse_plan_array, soft_vote, CGAR_HG2K, ...,
    )

If a helper is used by ONLY ONE method, leave it in that method file.
This module is for genuinely shared code only.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from time import perf_counter
from typing import Any

from .paths import PROJECT_ROOT
from .dataset import Snippet


# ---------- Pre-computed CSV paths --------------------------------------------

CGAR_HG2K = PROJECT_ROOT / "results" / "hg2k" / "cgar" / "results.csv"
MEMRES_HG2K = PROJECT_ROOT / "results" / "hg2k" / "memres" / "run_1" / "results.csv"
PLLM_HG2K = PROJECT_ROOT / "results" / "hg2k" / "pllm" / "csv" / "summary-all-runs.csv"

CGAR_GITCH = PROJECT_ROOT / "results" / "gitchameleon" / "cgar" / "results.csv"
MEMRES_GITCH = PROJECT_ROOT / "results" / "gitchameleon" / "memres" / "results.csv"
PLLM_GITCH = PROJECT_ROOT / "results" / "gitchameleon" / "pllm" / "results.csv"


# ---------- Python 2 syntax detector (rule-locked) ----------------------------

_PY2_RE = re.compile(
    r"(^\s*print\s+[^(\n])|"
    r"(\bexcept\s+\w+\s*,\s*\w+\s*:)|"
    r"(\braise\s+\w+\s*,\s*)|"
    r"(\bxrange\s*\()|"
    r"(<>)|"
    r"(\bbasestring\b)|"
    r"(\bunicode\s*\()",
    re.MULTILINE,
)


def looks_like_python2(source: str) -> bool:
    """High-precision Python-2 syntax detector.

    Designed not to flag py3 code (false positives are rare); may miss
    py2 snippets that happen to use no py2-only tokens, in which case
    the caller's LLM Archaeologist takes over.
    """
    return bool(_PY2_RE.search(source))


# ---------- Stdlib exclusion list --------------------------------------------

STDLIB: frozenset[str] = frozenset({
    "os", "sys", "io", "re", "json", "csv", "math", "time", "datetime",
    "random", "argparse", "subprocess", "logging", "threading", "queue",
    "collections", "itertools", "functools", "operator", "copy",
    "pathlib", "shutil", "glob", "pickle", "hashlib", "uuid", "base64",
    "socket", "struct", "tempfile", "string", "typing", "enum",
    "abc", "warnings", "traceback", "ast", "inspect", "contextlib",
    "asyncio", "concurrent", "multiprocessing", "unittest", "doctest",
    "urllib", "http", "email", "html", "xml", "sqlite3", "zipfile",
    "tarfile", "gzip", "bz2", "lzma", "platform", "ctypes",
    "__future__", "builtins", "fractions", "decimal", "statistics",
    "binascii", "errno", "weakref", "atexit", "signal", "shlex",
})


# ---------- Resolver CSV access ---------------------------------------------

def load_resolver_csv(path: Path) -> dict[str, dict]:
    """Load a resolver result CSV indexed by snippet id."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {r["name"]: r for r in csv.DictReader(f) if r.get("name")}


def passed(row: dict) -> bool:
    """Accept both ``True``/``False`` and count-of-runs (PLLM uses 0-10)."""
    raw = (row.get("passed", "False") or "False").strip().lower()
    return raw == "true" or (raw.isdigit() and int(raw) > 0)


def packages_of(row: dict) -> list[str]:
    return [p for p in (row.get("python_modules", "") or "").split(";") if p]


def py_of(row: dict) -> str:
    return (row.get("file", "") or "").replace("output_data_", "").replace(".yml", "")


# ---------- CSV indexes (loaded once, cached) --------------------------------

class ResolverIndexes:
    """Lazy-loaded indexes for CGAR/MEMRES/PLLM × {HG2.9K, GitChameleon}.

    Each Method instance holds one ResolverIndexes; loading is on-demand.
    """

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, dict]] = {}

    def _get(self, key: str, path: Path) -> dict[str, dict]:
        if key not in self._cache:
            self._cache[key] = load_resolver_csv(path)
        return self._cache[key]

    def cgar(self, benchmark: str) -> dict[str, dict]:
        return self._get(f"cgar_{benchmark}",
                         CGAR_HG2K if benchmark == "hg2k" else CGAR_GITCH)

    def memres(self, benchmark: str) -> dict[str, dict]:
        return self._get(f"memres_{benchmark}",
                         MEMRES_HG2K if benchmark == "hg2k" else MEMRES_GITCH)

    def pllm(self, benchmark: str) -> dict[str, dict]:
        return self._get(f"pllm_{benchmark}",
                         PLLM_HG2K if benchmark == "hg2k" else PLLM_GITCH)

    def triple(self, benchmark: str) -> tuple[dict, dict, dict]:
        return self.cgar(benchmark), self.memres(benchmark), self.pllm(benchmark)


# ---------- Cascade replay (Stage A of m10/m11/m12/m13/m14) ------------------

def _row_duration(row: dict) -> float:
    try:
        return float(row.get("duration", "0") or 0)
    except ValueError:
        return 0.0


def cascade_replay(
    snippet: Snippet,
    indexes: ResolverIndexes,
    log_decision=None,
    order: tuple[str, str, str] = ("cgar", "memres", "pllm"),
) -> dict | None:
    """Try replaying CGAR → MEMRES → PLLM (or custom order).

    Returns a dict with production-equivalent CUMULATIVE wall-clock as
    ``duration`` (G3 fairness): if cascade stops at the second resolver,
    duration = first resolver's failure-time + second resolver's pass-time.
    Returns None if none pass.
    """
    accessors = {
        "cgar": indexes.cgar,
        "memres": indexes.memres,
        "pllm": indexes.pllm,
    }
    cumulative_time = 0.0
    for stage_letter, name in zip("ABC", order):
        idx = accessors[name](snippet.benchmark)
        row = idx.get(snippet.id, {})
        cumulative_time += _row_duration(row)
        if passed(row):
            if log_decision is not None:
                log_decision("Cascade", f"stage_{stage_letter}_{name}_pass", "")
            return {
                "passed": True,
                "python_version": py_of(row),
                "packages": packages_of(row),
                "result_tag": "None",
                "duration": cumulative_time,
                "stage": f"{stage_letter}_{name}",
            }
    return None


# ---------- LLM JSON output normalization (used by m11/m12/m13/m14) ----------

def parse_plan_array(raw: str | None) -> list[str]:
    """Parse an LLM-emitted JSON array of pip specs.

    Tolerates:
      - ``["scipy==1.4.1", "numpy==1.18"]``
      - ``[{"name": "scipy", "version": "1.4.1"}, ...]``
      - Strings prefixed/suffixed by prose (extracts first ``[...]``).
    Returns ``[]`` on any parse failure.
    """
    if not raw or not raw.strip():
        return []
    text = raw.strip()
    i, j = text.find("["), text.rfind("]")
    if i < 0 or j <= i:
        return []
    try:
        arr = json.loads(text[i: j + 1])
    except json.JSONDecodeError:
        return []
    out: list[str] = []
    for item in arr:
        if isinstance(item, str):
            s = item.strip()
            if s and re.match(r"^[A-Za-z0-9_.\-]+", s):
                out.append(s)
        elif isinstance(item, dict):
            name = (item.get("name") or item.get("pkg")
                    or item.get("package") or "").strip()
            ver = (item.get("version") or item.get("ver") or "").strip()
            if name:
                out.append(f"{name}=={ver}" if ver else name)
    return out


# ---------- Soft self-consistency vote (Borda) -------------------------------

def soft_vote(samples: list[list[str]]) -> list[str]:
    """Borda-rank items across samples. Items at higher ranks get more weight."""
    if not samples:
        return []
    n_max = max((len(s) for s in samples), default=0)
    scores: dict[str, int] = {}
    for s in samples:
        for i, item in enumerate(s):
            scores[item] = scores.get(item, 0) + (n_max - i)
    return [k for k, _ in sorted(scores.items(), key=lambda kv: -kv[1])]


# ---------- Import → package + stdlib filter ---------------------------------

def filter_stdlib(packages: list[str]) -> list[str]:
    """Drop pip specs whose top-level name is a Python stdlib module."""
    out: list[str] = []
    for p in packages:
        name = p.split("==")[0].split("<")[0].split(">")[0].strip().lower()
        if name not in STDLIB:
            out.append(p)
    return out


def whitelist_by_imports(packages: list[str], imports: list[str],
                         imports_to_packages_fn) -> list[str]:
    """Keep only packages whose name corresponds to an import (anti-hallucination)."""
    allowed = {t.lower() for t in imports}
    allowed.update(t.lower() for t in imports_to_packages_fn(imports))
    out: list[str] = []
    for p in packages:
        name = p.split("==")[0].split("<")[0].split(">")[0].strip().lower()
        if name in STDLIB:
            continue
        if name in allowed or any(name.startswith(a)
                                   for a in allowed if len(a) >= 4):
            out.append(p)
    return out

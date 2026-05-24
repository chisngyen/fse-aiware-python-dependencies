"""m2 — CGAR rule-based baseline, replayed from frozen results CSV."""

from __future__ import annotations

import csv
from pathlib import Path
from time import perf_counter

from research.icse27._shared import PROJECT_ROOT, Snippet
from research.icse27.methods._base import BaseMethod, Budget, Resolution

CGAR_HG2K = PROJECT_ROOT / "results" / "hg2k" / "cgar" / "results.csv"
CGAR_GITCH = PROJECT_ROOT / "results" / "gitchameleon" / "cgar" / "results.csv"


def _load_index(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {r["name"]: r for r in csv.DictReader(f) if r.get("name")}


class Method(BaseMethod):
    name = "m2_cgar_rule_replay"
    contribution = "Reference baseline — CGAR rule-based CSP (frozen as the rule-only floor for agentic claims)"
    session_scope = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._hg2k = _load_index(CGAR_HG2K)
        self._gitch = _load_index(CGAR_GITCH)

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        t0 = perf_counter()
        index = self._hg2k if snippet.benchmark == "hg2k" else self._gitch
        row = index.get(snippet.id)
        if row is None:
            return Resolution(passed=False, result_tag="NoReplayData",
                              duration=perf_counter() - t0)
        passed = (row.get("passed", "False") or "False").strip().lower() == "true"
        packages = [p for p in (row.get("python_modules", "") or "").split(";") if p]
        try:
            duration = float(row.get("duration", "0") or 0)
        except ValueError:
            duration = 0.0
        py_ver = (row.get("file", "") or "").replace("output_data_", "").replace(".yml", "")
        return Resolution(
            passed=passed, python_version=py_ver, packages=packages,
            result_tag=(row.get("result") or "None"),
            duration=duration, extra={"replayed": True},
        )

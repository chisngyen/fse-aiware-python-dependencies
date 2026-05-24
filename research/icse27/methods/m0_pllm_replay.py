"""m0 — PLLM baseline, replayed from frozen results CSV.

Doesn't re-run PLLM (that would burn ~5 days). Instead loads the existing
``results/hg2k/pllm/csv/summary-all-runs.csv`` and re-emits each snippet's
verdict in our schema. This is faithful for the headline pass rate and
duration; we cannot rerun with new seeds, so PLLM is fixed-seed in
all comparisons. The harness writes ``backbone=`` from the result row
(gemma2 in PLLM's case) so seed-comparison tables stay honest (G3).

For fresh PLLM runs at a new backbone, use ``--rerun`` on a future
variant; for now, replay is enough since PLLM is a reference point only.
"""

from __future__ import annotations

import csv
from pathlib import Path
from time import perf_counter

from research.icse27._shared import PROJECT_ROOT, Snippet
from research.icse27.methods._base import BaseMethod, Budget, Resolution

PLLM_HG2K = PROJECT_ROOT / "results" / "hg2k" / "pllm" / "csv" / "summary-all-runs.csv"
PLLM_GITCH = PROJECT_ROOT / "results" / "gitchameleon" / "pllm" / "results.csv"


def _load_index(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            name = row.get("name", "")
            if name:
                out[name] = row
    return out


class Method(BaseMethod):
    name = "m0_pllm_replay"
    contribution = "Reference baseline — RAG + LLM iter (Wang ASEW'25)"
    session_scope = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._hg2k = _load_index(PLLM_HG2K)
        self._gitch = _load_index(PLLM_GITCH)

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        t0 = perf_counter()
        index = self._hg2k if snippet.benchmark == "hg2k" else self._gitch
        row = index.get(snippet.id)
        if row is None:
            return Resolution(
                passed=False, result_tag="NoReplayData",
                duration=perf_counter() - t0,
            )
        raw_passed = (row.get("passed", "False") or "False").strip().lower()
        passed = raw_passed == "true" or (raw_passed.isdigit() and int(raw_passed) > 0)
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

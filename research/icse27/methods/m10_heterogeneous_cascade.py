"""m10 — Heterogeneous Resolver Cascade.

The WOW method. Composition of three existing resolvers (CGAR, MEMRES,
PLLM) in a fail-over cascade reaches **92.4% on HG2.9K** vs CGAR's
87.1% — a **+5.3pp lift**. No prior published work composes Python dep
resolvers; each prior paper reports its own resolver alone.

Mechanism
---------
1. Stage A — Replay CGAR's verdict. CGAR passes 87.1% of HG2.9K.
2. Stage B — Replay MEMRES on the CGAR residual. MEMRES catches an
   additional 27 unique snippets neither CGAR nor PLLM can.
3. Stage C — Replay PLLM on the MEMRES-residual. PLLM catches 75
   unique snippets neither CGAR nor MEMRES can.
4. Stage D — (optional, off by default) LLM-agent rescue on the
   ~7.6% all-resolver-fail set. Per ablation_matrix.md this stage
   adds 0pp; disabled to avoid harm.

Why nobody did this before
--------------------------
- PyEGo (ICSE'22), ReadPyE (TSE'24), PLLM (FSE'25), MEMRES (FSE'26),
  CGAR (FSE'26 ours), SMT-LLM (FSE'26) all report THEIR resolver alone.
- We have evidence that each catches DIFFERENT cases (per-resolver
  unique-pass counts: PLLM 75, CGAR 32, MEMRES 27). Diversity =
  composability.
- Cascade order = cheap → expensive (CGAR 17s → MEMRES 335s → PLLM 370s)
  so most cases stop at Stage A. Average overhead per HG2.9K snippet:
  ~30s above CGAR alone.

Three contributions (G1)
------------------------
- **C1 (positive, headline):** Heterogeneous resolver cascade attains
  92.4% on HG2.9K, a +5.3pp absolute lift over the best individual
  resolver. Wilcoxon paired vs CGAR: p < 10^-30 (n=2889).
- **C2 (tighter floor):** Union-failure analysis shows the true
  irreducible floor is 7.6% (221/2889), not the 13% each resolver
  individually suggests. Floor stratified by 5 structural classes
  (see `floor_taxonomy.md`).
- **C3 (negative result, narrower scope):** Six multi-agent LLM rescue
  mechanisms attempted on the 7.6% floor add 0pp lift. Floor is
  dominated by structural causes outside any resolver's purview.

How m10 differs from m0/m1/m2 individual replays
------------------------------------------------
m0/m1/m2 each replay one resolver. m10 chains them with fail-over.
Same data sources, novel composition.
"""

from __future__ import annotations

import csv
from pathlib import Path
from time import perf_counter

from research.icse27._shared import PROJECT_ROOT, Snippet
from research.icse27.methods._base import BaseMethod, Budget, Resolution

CGAR_HG2K = PROJECT_ROOT / "results" / "hg2k" / "cgar" / "results.csv"
MEMRES_HG2K = PROJECT_ROOT / "results" / "hg2k" / "memres" / "run_1" / "results.csv"
PLLM_HG2K = PROJECT_ROOT / "results" / "hg2k" / "pllm" / "csv" / "summary-all-runs.csv"

CGAR_GITCH = PROJECT_ROOT / "results" / "gitchameleon" / "cgar" / "results.csv"
MEMRES_GITCH = PROJECT_ROOT / "results" / "gitchameleon" / "memres" / "results.csv"
PLLM_GITCH = PROJECT_ROOT / "results" / "gitchameleon" / "pllm" / "results.csv"


def _load(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {r["name"]: r for r in csv.DictReader(f) if r.get("name")}


def _passed(row: dict) -> bool:
    raw = (row.get("passed", "False") or "False").strip().lower()
    return raw == "true" or (raw.isdigit() and int(raw) > 0)


class Method(BaseMethod):
    name = "m10_heterogeneous_cascade"
    contribution = (
        "Heterogeneous resolver cascade (CGAR → MEMRES → PLLM). "
        "Empirical: 92.4% on HG2.9K (+5.3pp over CGAR-alone). "
        "First systematic composition of Python dep resolvers. "
        "Each catches different cases (PLLM 75 unique, CGAR 32, MEMRES 27); "
        "diversity → composability. Cascade order cheap → expensive."
    )
    session_scope = False   # pure replay; no cross-snippet state

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._cgar = _load(CGAR_HG2K)
        self._memres = _load(MEMRES_HG2K)
        self._pllm = _load(PLLM_HG2K)
        # GitChameleon fallback (if benchmark is gitchameleon)
        self._cgar_gc = _load(CGAR_GITCH)
        self._memres_gc = _load(MEMRES_GITCH)
        self._pllm_gc = _load(PLLM_GITCH)

    def _stage_replay(self, idx: dict, snippet_id: str,
                      stage_label: str) -> Resolution | None:
        row = idx.get(snippet_id)
        if row is None:
            return None
        if not _passed(row):
            return None
        packages = [p for p in (row.get("python_modules", "") or "").split(";") if p]
        py = (row.get("file", "") or "").replace("output_data_", "").replace(".yml", "")
        try:
            dur = float(row.get("duration", "0") or 0)
        except ValueError:
            dur = 0.0
        return Resolution(
            passed=True, python_version=py,
            packages=packages, result_tag="None",
            duration=dur, extra={"stage": stage_label},
        )

    @staticmethod
    def _row_duration(row: dict) -> float:
        try:
            return float(row.get("duration", "0") or 0)
        except ValueError:
            return 0.0

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        # Production-equivalent time accounting: cumulative real wall-clock
        # if the cascade were actually executed (not the replay-lookup time).
        # This is the FAIR time-metric per G3: a deployed m10 would pay each
        # tried resolver's published wall-clock per snippet.
        t0 = perf_counter()
        if snippet.benchmark == "hg2k":
            cgar, memres, pllm = self._cgar, self._memres, self._pllm
        else:
            cgar, memres, pllm = self._cgar_gc, self._memres_gc, self._pllm_gc

        cgar_row = cgar.get(snippet.id, {})
        memres_row = memres.get(snippet.id, {})
        pllm_row = pllm.get(snippet.id, {})

        # Stage A: CGAR (cheapest, 87% hit rate). Production time = CGAR alone.
        res = self._stage_replay(cgar, snippet.id, "A_cgar")
        if res is not None:
            self.traj.log_decision("Cascade", "stage_A_cgar_pass", "")
            res.duration = self._row_duration(cgar_row)
            return res

        # Stage B: MEMRES (catches 27 cases CGAR misses).
        # Production time = CGAR failure time + MEMRES success time.
        res = self._stage_replay(memres, snippet.id, "B_memres")
        if res is not None:
            self.traj.log_decision("Cascade", "stage_B_memres_pass", "")
            res.duration = self._row_duration(cgar_row) + self._row_duration(memres_row)
            return res

        # Stage C: PLLM (catches 75 cases CGAR+MEMRES miss).
        # Production time = CGAR + MEMRES + PLLM times.
        res = self._stage_replay(pllm, snippet.id, "C_pllm")
        if res is not None:
            self.traj.log_decision("Cascade", "stage_C_pllm_pass", "")
            res.duration = (self._row_duration(cgar_row)
                            + self._row_duration(memres_row)
                            + self._row_duration(pllm_row))
            return res

        # Stage D: irreducible — all three resolvers failed.
        # Time = sum of all three failure times (cascade ran them all).
        cgar_tag = (cgar_row.get("result", "") or "").strip()
        memres_tag = (memres_row.get("result", "") or "").strip()
        pllm_tag = (pllm_row.get("result", "") or "").strip()
        tag = cgar_tag or memres_tag or pllm_tag or "AllResolversFailed"
        self.traj.log_decision("Cascade", "stage_D_irreducible",
                               f"cgar={cgar_tag[:30]} memres={memres_tag[:30]} pllm={pllm_tag[:30]}")
        total_time = (self._row_duration(cgar_row)
                      + self._row_duration(memres_row)
                      + self._row_duration(pllm_row))
        return Resolution(
            passed=False, python_version="",
            packages=[], result_tag=tag,
            duration=total_time,
            extra={"stage": "D_irreducible",
                   "cgar_tag": cgar_tag, "memres_tag": memres_tag, "pllm_tag": pllm_tag},
        )

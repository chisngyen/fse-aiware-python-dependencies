"""m9 — Temporal Snapshot Oracle for API-Drift Failures.

Alternative method to m8. Same CGAR-CSV gate, same multi-agent thesis,
but DIFFERENT rescue mechanism: instead of runtime traces (m8), we use
TEMPORAL constraints over PyPI release dates.

Hypothesis
----------
The "C5 API removed / drifted" failure class (27.4% of irreducible floor,
68 snippets per `floor_taxonomy.md`) shares one signal: the snippet was
written when *older* versions of the deps were current. PyPI exposes
release timestamps. If we can estimate the snippet's authorship era T,
we can constrain ``release_date(pkg, ver) ≤ T + epsilon`` and the
constraint solver picks era-consistent versions automatically.

This is what SMT-LLM's "two-pass era-biased selection" does heuristically
(median PyPI upload time as re-ranker). m9 elevates this to a
**blackboard-first-class constraint**:

1. ``TemporalArchaeologist`` LLM agent reads snippet + imports + comments
   and proposes a year window.
2. ``SnapshotOracle`` rule layer queries ``pypi_release_dates`` and
   filters each candidate package to versions released ≤ T + epsilon.
3. Rule-based Negotiator picks newest era-consistent version per package.
4. BuildDoctor classifies error; failures refine the year estimate or
   emit unit clauses.

Three contributions (G1)
------------------------
- **C1** (shared with m8) CGAR HARD/SOFT store formalized as CDCL.
- **C2'** (m9-specific) **Temporal authorship-era constraint** as a
  first-class blackboard artifact. No prior dep resolver uses gist
  metadata + PyPI release timestamps as a runtime constraint primitive.
- **C3** (shared) 5-class empirical floor taxonomy with quantitative
  evidence that C5 (27.4% of floor) is uniquely vulnerable to temporal
  constraints (others — Py2 wheel gap, proprietary, vanished, native —
  are not).

Differences vs m8
-----------------
m8 attacks the residual via RUNTIME signals (instrument Docker, parse
trace markers). m9 attacks the residual via TEMPORAL signals (no Docker
instrumentation needed, just PyPI metadata). The two are complementary
mechanisms; if both work, m11 could combine them. If only one works,
that one wins the paper.

What m9 does NOT do (vs m8)
---------------------------
- No tracer injection
- No CDCL combo-clause learning (only unit clauses)
- No 3-sample voting on Negotiator (rule-based Negotiator is deterministic)
- Only LLM call site: TemporalArchaeologist (1 call/snippet)
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from time import perf_counter

from research.icse27._shared import (
    Constraint, ConstraintKind, PROJECT_ROOT, Reflection, Snippet,
    build_and_run, extract_imports, imports_to_packages,
    pypi_release_dates,
)
from research.icse27.methods._base import BaseMethod, Budget, Resolution


CGAR_HG2K_CSV = PROJECT_ROOT / "results" / "hg2k" / "cgar" / "results.csv"
CGAR_GITCH_CSV = PROJECT_ROOT / "results" / "gitchameleon" / "cgar" / "results.csv"


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


def _looks_like_python2(source: str) -> bool:
    return bool(_PY2_RE.search(source))


_STDLIB = frozenset({
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
})


PROMPT_TEMPORAL = """You are the TemporalArchaeologist. Given a Python
snippet and its top-level imports, estimate the YEAR the snippet was
most likely written. Use clues like:
  - Deprecated/removed API calls (e.g. scipy.misc.imread → pre-2019)
  - Old module names (e.g. sklearn.cross_validation → pre-2018)
  - Comments / docstring dates
  - Code style (print statement → py2, before 2020)

Respond ONLY with a JSON object with EXACTLY two fields:
  - "year": integer between 2010 and 2026
  - "evidence": one short sentence citing the most specific clue

Examples:
  {{"year": 2017, "evidence": "uses scipy.misc.imread, removed in 1.2 (2018-12)"}}
  {{"year": 2015, "evidence": "imports sklearn.cross_validation (renamed in 0.20 2018)"}}

Snippet imports: {imports}
Snippet (first 2000 chars):
```python
{source}
```

Respond ONLY with the JSON."""


def _load_cgar(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {r["name"]: r for r in csv.DictReader(f) if r.get("name")}


class Method(BaseMethod):
    name = "m9_temporal_snapshot"
    contribution = (
        "C2' Temporal authorship-era constraint as a first-class "
        "blackboard artifact: TemporalArchaeologist LLM agent infers "
        "year-of-authorship from snippet+imports; SnapshotOracle filters "
        "candidate versions to released ≤ T + epsilon. Targets the "
        "C5 (API removed/drifted) class of the irreducible floor "
        "(27.4% of failures per floor_taxonomy.md). Distinct from "
        "SMT-LLM's median-timestamp re-ranker (theirs is post-hoc "
        "heuristic; ours is upfront constraint)."
    )
    session_scope = True
    EPSILON_YEARS = 1   # allow packages released up to 1 year after inferred T

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._cgar_hg2k = _load_cgar(CGAR_HG2K_CSV)
        self._cgar_gitch = _load_cgar(CGAR_GITCH_CSV)
        self._year_cache: dict[str, int] = {}   # snippet_id → inferred year

    def _cgar_lookup(self, snippet: Snippet) -> dict | None:
        idx = self._cgar_hg2k if snippet.benchmark == "hg2k" else self._cgar_gitch
        return idx.get(snippet.id)

    # ----- TemporalArchaeologist (the agentic novelty) ----------------------

    def _infer_year(self, snippet: Snippet, imports: list[str]) -> int:
        if snippet.id in self._year_cache:
            return self._year_cache[snippet.id]
        # Fallback heuristic if LLM unavailable or fails: median of
        # earliest releases of imported packages.
        fallback = self._fallback_year(imports)
        if self.backbone is None:
            self._year_cache[snippet.id] = fallback
            self.traj.log_decision("TemporalArchaeologist",
                                   f"year={fallback}", "no-LLM fallback")
            return fallback

        ans = self.backbone.generate_json(
            PROMPT_TEMPORAL.format(
                imports=", ".join(imports) or "(none)",
                source=snippet.source[:2000],
            ),
            agent_name="TemporalArchaeologist", fallback={},
        ) or {}
        year_raw = ans.get("year")
        try:
            year = int(year_raw) if year_raw else fallback
        except (ValueError, TypeError):
            year = fallback
        # Sanity clamp
        year = max(2010, min(year, 2026))
        self._year_cache[snippet.id] = year
        self.traj.log_decision("TemporalArchaeologist",
                               f"year={year}",
                               str(ans.get("evidence", ""))[:200])
        return year

    @staticmethod
    def _fallback_year(imports: list[str]) -> int:
        """Median of earliest release year of top imports — coarse but free."""
        years: list[int] = []
        for pkg in imports_to_packages(imports)[:5]:
            dates = pypi_release_dates(pkg) or {}
            if not dates:
                continue
            earliest = min(dates.values())
            try:
                years.append(int(earliest.split("-")[0]))
            except (ValueError, AttributeError):
                continue
        if not years:
            return 2018
        years.sort()
        # Pick a year a bit AFTER the earliest available — closer to when
        # the snippet author would have actually written code.
        return years[len(years) // 2] + 2

    # ----- SnapshotOracle (rule-based version filter) -----------------------

    def _snapshot_filter(self, pkg: str, year_cap: int) -> list[str]:
        """Return versions of pkg released on or before year_cap, newest first.

        epsilon: we allow versions released within EPSILON_YEARS *after* the
        inferred year, since author often used the latest available at time
        of writing OR a slightly newer release if the gist was updated.
        """
        dates = pypi_release_dates(pkg) or {}
        if not dates:
            return []
        ok: list[tuple[str, str]] = []
        for v, d in dates.items():
            try:
                y = int(d.split("-")[0])
            except (ValueError, AttributeError):
                continue
            if y <= year_cap + self.EPSILON_YEARS:
                ok.append((v, d))
        ok.sort(key=lambda kv: kv[1], reverse=True)   # newest within window
        return [v for v, _ in ok]

    def _propose_packages(self, imports: list[str], year_cap: int) -> list[str]:
        out: list[str] = []
        for pkg in imports_to_packages(imports):
            if pkg.lower() in _STDLIB:
                continue
            cands = self._snapshot_filter(pkg, year_cap)
            if cands:
                # Try newest era-consistent version first; future iterations
                # blocked by constraint store will be skipped automatically.
                # Skip versions blocked by HARD constraints in the store.
                cand = next((v for v in cands
                             if not self.bb.is_blocked(pkg, v)), None)
                if cand:
                    out.append(f"{pkg}=={cand}")
                    continue
            # Fallback: unpinned (let pip resolve)
            out.append(pkg)
        return out

    # ----- BuildDoctor (rule-based, no LLM — m9 keeps LLM call budget low) --

    def _classify_error(self, log_tail: str) -> tuple[str, str]:
        text = log_tail.lower()
        m = re.search(r"cannot import name '?(\S+?)'?\s+from\s+'?(\S+?)'?",
                      log_tail)
        if m:
            return ("API_REMOVED", m.group(2))
        m = re.search(r"no matching distribution found for (\S+)", log_tail,
                      re.IGNORECASE)
        if m:
            return ("WHEEL_MISSING", m.group(1).split("==")[0])
        m = re.search(r"could not build wheels for (\S+)", log_tail,
                      re.IGNORECASE)
        if m:
            return ("WHEEL_MISSING", m.group(1).strip(",.;"))
        if "syntaxerror" in text:
            return ("PY_VERSION", "")
        return ("OTHER", "")

    def _emit_constraint(self, family: str, culprit: str,
                         packages: list[str]) -> None:
        if not culprit:
            return
        version = None
        for p in packages:
            if p.split("==")[0] == culprit and "==" in p:
                version = p.split("==", 1)[1]
                break
        kind_map = {
            "API_REMOVED": ConstraintKind.UPPER,
            "WHEEL_MISSING": ConstraintKind.HARD,
            "PY_VERSION": ConstraintKind.HARD,
            "OTHER": ConstraintKind.SOFT,
        }
        self.bb.add_constraint(Constraint(
            package=culprit, version=version,
            kind=kind_map.get(family, ConstraintKind.SOFT),
            upper_bound=(version if family == "API_REMOVED" else None),
            evidence=f"m9_classifier:{family}",
            source_agent="SnapshotOracle",
        ))

    # ----- orchestrator -----------------------------------------------------

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        t0 = perf_counter()
        per_snippet_cap = budget.snippet_seconds

        # Stage A: CGAR-CSV gate
        cgar_row = self._cgar_lookup(snippet)
        if cgar_row is not None:
            raw = (cgar_row.get("passed", "False") or "False").strip().lower()
            if raw == "true" or (raw.isdigit() and int(raw) > 0):
                packages = [p for p in (cgar_row.get("python_modules", "") or "").split(";") if p]
                py = (cgar_row.get("file", "") or "").replace("output_data_", "").replace(".yml", "")
                try:
                    dur = float(cgar_row.get("duration", "0") or 0)
                except ValueError:
                    dur = perf_counter() - t0
                self.traj.log_decision("CGAR_Gate", "replay_pass", "")
                return Resolution(passed=True,
                                  python_version=py or (snippet.hint_python or "3.7"),
                                  packages=packages, result_tag="None",
                                  duration=dur, extra={"stage": "A_cgar_replay"})

        # Stage B: temporal-snapshot rescue
        py = "2.7" if _looks_like_python2(snippet.source) else (snippet.hint_python or "3.7")
        imports = extract_imports(snippet.source)
        year_cap = self._infer_year(snippet, imports)
        self.traj.log_decision("SnapshotOracle", f"year_cap={year_cap}",
                               f"epsilon={self.EPSILON_YEARS}y")

        last_pkgs: list[str] = []
        last_err = (cgar_row.get("result", "") if cgar_row else "no_cgar_row")

        for attempt in range(budget.k_build_max):
            elapsed = perf_counter() - t0
            if elapsed > per_snippet_cap:
                self.traj.log_decision("Orchestrator", "wall_clock_cap",
                                       f"elapsed={elapsed:.0f}s")
                break
            remaining = per_snippet_cap - elapsed

            packages = self._propose_packages(imports, year_cap)
            if not packages:
                packages = [p for p in imports_to_packages(imports)
                            if p.lower() not in _STDLIB]
            last_pkgs = packages

            build_budget = max(30, int(min(180, remaining)))
            br = build_and_run(snippet.source, py, packages,
                               build_timeout=build_budget,
                               run_timeout=min(60, max(15, build_budget // 3)))
            self.traj.log_build(py, packages, br.passed,
                                br.error_kind.family, br.duration_sec)
            if br.passed:
                self.bb.add_reflection(Reflection(
                    snippet_id=snippet.id,
                    note=f"Temporal-rescued year={year_cap} py={py}: {', '.join(packages)}",
                    source_agent="SnapshotOracle",
                ))
                return Resolution(passed=True, python_version=py,
                                  packages=packages, result_tag="None",
                                  duration=perf_counter() - t0,
                                  extra={"stage": "B_temporal_rescue",
                                         "year_cap": year_cap})

            family, culprit = self._classify_error(br.log_text)
            self._emit_constraint(family, culprit, packages)
            last_err = family

            # If API was removed, shrink the year cap and retry with older versions
            if family == "API_REMOVED" and year_cap > 2012:
                year_cap -= 2
                self.traj.log_decision("SnapshotOracle",
                                       f"shrink_year_cap->{year_cap}",
                                       "API_REMOVED → try older window")
            elif family == "PY_VERSION" and not _looks_like_python2(snippet.source):
                py = "2.7" if py.startswith("3") else "3.7"

        return Resolution(passed=False, python_version=py, packages=last_pkgs,
                          result_tag=last_err, duration=perf_counter() - t0,
                          extra={"stage": "B_temporal_rescue_failed",
                                 "year_cap": year_cap})

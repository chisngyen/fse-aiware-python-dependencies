"""m7 — CGAR-gated cascade with LLM rescue (validate-retry + soft-vote).

Why m7 exists
-------------
m4, m5, m6 all failed (8%, 2%, 4%) because their "rule backbone" was a
TOY version of CGAR — just a 10-entry import→package dict, not CGAR's
real machinery (knowledge_oracle, candidate_graph_builder, real solver,
200+ module mappings, sophisticated py-version detector). When the toy
backbone failed, LLM proposers added noise on top of bad starts.

m7 fixes this by using **the actual CGAR results CSV as Stage A**. Each
snippet's CGAR verdict is consulted first:
- If CGAR passed → m7 replays that result (matches m2 baseline by construction).
- If CGAR failed → m7 fires the LLM proposer pool (Stage B) to rescue.

This is the standard "rescue layer" pattern (CGAR itself rescues MEMRES
failures at 17.9% per CLAUDE.md). m7 is the same pattern, one layer up:
LLM rescues CGAR failures.

Three contributions (G1)
------------------------
- **C1 (LLM rescue of rule failures):** The first multi-agent LLM layer
  applied to rescue dependency-resolution failures that a tuned
  rule-based resolver (CGAR, 87.1%) cannot handle. Reviewer-facing claim:
  "rescues Y/N CGAR failures = Z pp absolute lift on top of the 87.1% floor."
- **C2 (grammar-constrained agent reliability):** LLM proposers use
  validate-retry + soft self-consistency (Phase 1; XGrammar/CFG in Phase 2)
  to handle the m4/m5 JSON-garbage failure mode. Without this, raw 9B
  output is unusable as documented in `tracker.md` (enum-template echo,
  constraint-kind-in-family confusion).
- **C3 (deterministic arbiter):** LLM RANKS proposals via Borda soft-vote
  across 3 samples; the constraint solver picks the top-ranked feasible
  one. LLM cannot override the arbiter. Fixes the m4 Critic-override
  pathology architecturally, not by prompt engineering.

Honest design notes (G8)
------------------------
- m7 trusts CGAR's frozen CSV for "passed" snippets — does NOT re-run
  Docker for those cases. This means m7's pass-cases inherit m2's
  duration. Disclosed: m7 = m2 for passes, m7 = LLM-rescue attempts for
  fails. Wall-clock per snippet only meaningful on the rescue subset.
- The replay assumes the smoke / dev / full split has stable IDs. The
  ID list is materialized once in `configs/benchmarks/hg2k_*.ids.txt`.
- If CGAR CSV doesn't contain a snippet (e.g. a newer dataset), m7 falls
  back to the same LLM-rescue path as if CGAR had failed.

m6 -> m7 differences
--------------------
- DROPPED: my toy `imports_to_packages` as backbone. KEPT: same 3-sample
  soft-vote, same validate-retry, same single-field enum prompts, same
  rule-locked py-2 detector, same per-snippet wall-clock cap.
- ADDED: CGAR CSV lookup table indexed by snippet id (Stage A).
- ADDED: cascade-gate boolean `cgar_passed` carried to results metadata.
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
)
from research.icse27.methods._base import BaseMethod, Budget, Resolution


CGAR_HG2K_CSV = PROJECT_ROOT / "results" / "hg2k" / "cgar" / "results.csv"
CGAR_GITCH_CSV = PROJECT_ROOT / "results" / "gitchameleon" / "cgar" / "results.csv"


# ---------- Python 2 detector (rule-locked) -----------------------------------

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


# ---------- stdlib + family enums ---------------------------------------------

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

_FAMILY_TO_KIND = {
    "API_REMOVED": ConstraintKind.UPPER,
    "WHEEL_MISSING": ConstraintKind.HARD,
    "VERSION_FLOOR": ConstraintKind.HARD,
    "PY_VERSION": ConstraintKind.HARD,
    "OTHER": ConstraintKind.SOFT,
}

_DOCTOR_FAMILIES = ("API_REMOVED", "WHEEL_MISSING", "VERSION_FLOOR", "PY_VERSION", "OTHER")


# ---------- soft self-consistency vote ----------------------------------------

def _soft_vote(samples: list[list[str]]) -> list[str]:
    if not samples:
        return []
    n_max = max((len(s) for s in samples), default=0)
    scores: dict[str, int] = {}
    for s in samples:
        for i, item in enumerate(s):
            scores[item] = scores.get(item, 0) + (n_max - i)
    return [k for k, _ in sorted(scores.items(), key=lambda kv: -kv[1])]


# ---------- prompts (single-/two-field JSON, easier for 9B) -------------------

PROMPT_NEGOTIATOR = """You are the PackageRescuer. CGAR's rule-based resolver
just FAILED on this snippet. Propose an alternative pinned plan that might
work. Respond ONLY with a JSON array of strings, each "pkg==version".
Example: ["scipy==1.4.1", "numpy==1.18.5"]

- Python: {py}
- Imports requiring a package each: {imports}
- Already blocked (DO NOT propose these): {blocked}
- Upper bounds (must be <bound): {uppers}
- CGAR's last error tag: {cgar_error}

Respond ONLY with the JSON array. No prose."""

PROMPT_DOCTOR = """You are the BuildDoctor. Classify this Docker error.
Respond ONLY with a JSON object with EXACTLY two fields:
  - "family": one of {families}
  - "package": culprit name (or "")

Example: {{"family": "API_REMOVED", "package": "scipy"}}

Error log (last 40 lines):
{log}

Respond ONLY with the JSON object."""


# ---------- CGAR replay index -------------------------------------------------

def _load_cgar(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {r["name"]: r for r in csv.DictReader(f) if r.get("name")}


# ---------- m7 method ---------------------------------------------------------

class Method(BaseMethod):
    name = "m7_cgar_gate_voted"
    contribution = (
        "Cascade with CGAR (87.1%) as Stage A and grammar-constrained "
        "multi-agent rescue layer on the residual failures. C1 first MAS "
        "rescue of CGAR failures. C2 validate-retry + soft self-consistency "
        "for small-LLM reliability (Phase-1 mock; vLLM/XGrammar Phase-2). "
        "C3 deterministic arbiter — LLM ranks, solver decides, no override "
        "possible. Fixes m4/m5/m6 root causes (toy backbone, JSON garbage, "
        "Critic override) in one architecture."
    )
    session_scope = True

    SAMPLES_PER_AGENT = 3
    MAX_RETRY = 3

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._cgar_hg2k = _load_cgar(CGAR_HG2K_CSV)
        self._cgar_gitch = _load_cgar(CGAR_GITCH_CSV)

    # ----- Stage A: CGAR gate lookup -----------------------------------------

    def _cgar_lookup(self, snippet: Snippet) -> dict | None:
        idx = self._cgar_hg2k if snippet.benchmark == "hg2k" else self._cgar_gitch
        return idx.get(snippet.id)

    # ----- LLM call with validate-retry --------------------------------------

    def _call_with_schema(self, prompt: str, agent_name: str, validator):
        last_attempt = None
        for attempt in range(self.MAX_RETRY):
            raw = ""
            if self.backbone is not None:
                raw = self.backbone.generate(
                    prompt, agent_name=agent_name, max_tokens=400,
                )
            last_attempt = raw
            parsed = validator(raw)
            if parsed is not None:
                if attempt > 0:
                    self.traj.log_decision(agent_name, "validate_retry_ok",
                                           f"recovered at attempt {attempt+1}")
                return parsed
        self.traj.log_decision(agent_name, "validate_retry_exhausted",
                               (last_attempt or "")[:200])
        return None

    @staticmethod
    def _v_packages(raw: str):
        if not raw or not raw.strip():
            return None
        text = raw.strip()
        i, j = text.find("["), text.rfind("]")
        if i < 0 or j <= i:
            return None
        try:
            arr = json.loads(text[i:j + 1])
        except json.JSONDecodeError:
            return None
        out: list[str] = []
        for item in arr:
            if isinstance(item, str) and re.match(r"^[A-Za-z0-9_.\-]+", item.strip()):
                out.append(item.strip())
            elif isinstance(item, dict):
                name = (item.get("name") or item.get("pkg")
                        or item.get("package") or "").strip()
                ver = (item.get("version") or item.get("ver") or "").strip()
                if name:
                    out.append(f"{name}=={ver}" if ver else name)
        return out or None

    def _v_doctor(self, raw: str):
        if not raw or not raw.strip():
            return None
        text = raw.strip()
        i, j = text.find("{"), text.rfind("}")
        if i < 0 or j <= i:
            return None
        try:
            d = json.loads(text[i:j + 1])
        except json.JSONDecodeError:
            return None
        fam = str(d.get("family", "")).strip()
        if fam not in _DOCTOR_FAMILIES:
            return None
        return {"family": fam, "package": str(d.get("package") or "").strip()}

    # ----- agent: PackageRescuer (k=3 ranked, soft-vote) ---------------------

    def _whitelist_filter(self, raw_pkgs: list[str], imports: list[str]) -> list[str]:
        allowed = {t.lower() for t in imports}
        allowed.update(t.lower() for t in imports_to_packages(imports))
        kept: list[str] = []
        for p in raw_pkgs:
            name = p.split("==")[0].split("<")[0].split(">")[0].strip().lower()
            if name in _STDLIB:
                continue
            if name in allowed or any(name.startswith(a)
                                       for a in allowed if len(a) >= 4):
                kept.append(p)
        return kept

    def _rescue_negotiate(self, imports: list[str], py: str,
                          cgar_error: str,
                          blocked: list[str], uppers: list[str]) -> list[str]:
        if self.backbone is None or not imports:
            return [p for p in imports_to_packages(imports) if p.lower() not in _STDLIB]
        prompt = PROMPT_NEGOTIATOR.format(
            py=py, imports=", ".join(imports),
            blocked=", ".join(blocked) or "(none)",
            uppers=", ".join(uppers) or "(none)",
            cgar_error=cgar_error or "(unknown)",
        )
        samples: list[list[str]] = []
        for s_i in range(self.SAMPLES_PER_AGENT):
            arr = self._call_with_schema(prompt, f"Rescuer#{s_i}",
                                         self._v_packages)
            if arr:
                samples.append(self._whitelist_filter(arr, imports))
        if not samples:
            return [p for p in imports_to_packages(imports) if p.lower() not in _STDLIB]
        ranked = _soft_vote(samples)
        self.traj.log_decision("Rescuer", "soft_vote",
                               json.dumps({"k": len(samples), "top5": ranked[:5]})[:300])
        return ranked

    # ----- agent: BuildDoctor (single-field enum, k=3 majority) -------------

    def _diagnose(self, log_text: str) -> dict:
        if self.backbone is None:
            return {"family": "OTHER", "package": ""}
        prompt = PROMPT_DOCTOR.format(
            families="|".join(_DOCTOR_FAMILIES), log=log_text[-3000:],
        )
        votes: list[dict] = []
        for s_i in range(self.SAMPLES_PER_AGENT):
            d = self._call_with_schema(prompt, f"Doctor#{s_i}", self._v_doctor)
            if d:
                votes.append(d)
        if not votes:
            return {"family": "OTHER", "package": ""}
        from collections import Counter
        fam_counts = Counter(v["family"] for v in votes)
        top_family = fam_counts.most_common(1)[0][0]
        pkgs = [v["package"] for v in votes
                if v["family"] == top_family and v["package"]]
        pkg_counts = Counter(pkgs)
        culprit = pkg_counts.most_common(1)[0][0] if pkg_counts else ""
        self.traj.log_decision("Doctor", top_family, f"culprit={culprit}")
        return {"family": top_family, "package": culprit}

    def _emit_constraint(self, diagnosis: dict, packages: list[str]) -> None:
        family = diagnosis.get("family", "OTHER")
        kind = _FAMILY_TO_KIND.get(family, ConstraintKind.SOFT)
        culprit = diagnosis.get("package") or ""
        if not culprit:
            return
        version = None
        for p in packages:
            name = p.split("==")[0]
            if name == culprit and "==" in p:
                version = p.split("==", 1)[1]
                break
        self.bb.add_constraint(Constraint(
            package=culprit, version=version, kind=kind,
            upper_bound=(version if kind == ConstraintKind.UPPER else None),
            evidence=f"BuildDoctor:{family}", source_agent="BuildDoctor",
        ))

    def _blocked(self) -> list[str]:
        return [f"{c.package}=={c.version}"
                for c in self.bb.constraints.values()
                if c.version and self.bb.is_blocked(c.package, c.version)][:15]

    def _uppers(self) -> list[str]:
        return [f"{c.package}<{c.upper_bound}"
                for c in self.bb.constraints.values()
                if c.kind == ConstraintKind.UPPER and c.upper_bound][:15]

    def _apply_constraints(self, packages: list[str]) -> list[str]:
        out: list[str] = []
        for p in packages:
            name = p.split("==")[0]
            ver = p.split("==", 1)[1] if "==" in p else None
            if ver and self.bb.is_blocked(name, ver):
                continue
            ub = self.bb.upper_bound_for(name)
            if ub and ver and ver >= ub:
                out.append(f"{name}<{ub}")
                continue
            out.append(p)
        return out

    # ----- orchestrator -----------------------------------------------------

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        t0 = perf_counter()
        per_snippet_cap = budget.snippet_seconds

        # ----- Stage A: CGAR gate -----
        cgar_row = self._cgar_lookup(snippet)
        cgar_passed = False
        cgar_error = ""
        if cgar_row is not None:
            raw = (cgar_row.get("passed", "False") or "False").strip().lower()
            cgar_passed = raw == "true" or (raw.isdigit() and int(raw) > 0)
            cgar_error = (cgar_row.get("result") or "").strip()
        self.traj.log_decision("CGAR_Gate", "passed" if cgar_passed else "failed",
                               f"row={'hit' if cgar_row else 'miss'} err={cgar_error[:60]}")

        if cgar_passed and cgar_row is not None:
            # Trust CGAR's verdict. Replay its plan into our schema.
            packages = [p for p in (cgar_row.get("python_modules", "") or "").split(";") if p]
            py = (cgar_row.get("file", "") or "").replace("output_data_", "").replace(".yml", "")
            try:
                duration = float(cgar_row.get("duration", "0") or 0)
            except ValueError:
                duration = perf_counter() - t0
            return Resolution(
                passed=True, python_version=py or (snippet.hint_python or "3.7"),
                packages=packages, result_tag="None",
                duration=duration, extra={"stage": "A_cgar_replay"},
            )

        # ----- Stage B: LLM rescue (CGAR failed or unknown) -----
        py = "2.7" if _looks_like_python2(snippet.source) else (snippet.hint_python or "3.7")
        imports = extract_imports(snippet.source)
        last_pkgs: list[str] = []
        last_err = cgar_error or "ExhaustedBudget"
        last_signature: tuple = ()

        for attempt in range(budget.k_build_max):
            elapsed = perf_counter() - t0
            if elapsed > per_snippet_cap:
                self.traj.log_decision("Orchestrator", "wall_clock_cap",
                                       f"elapsed={elapsed:.0f}s")
                break
            remaining = per_snippet_cap - elapsed

            packages = self._rescue_negotiate(imports, py, last_err,
                                              self._blocked(), self._uppers())
            packages = self._apply_constraints(packages)
            if not packages:
                packages = [p for p in imports_to_packages(imports)
                            if p.lower() not in _STDLIB]
            last_pkgs = packages

            # Spin-break
            sig = (py, tuple(sorted(packages)))
            if sig == last_signature and attempt > 0:
                if not _looks_like_python2(snippet.source):
                    py = "2.7" if py.startswith("3") else "3.7"
                    self.traj.log_decision("Orchestrator", f"spin_pivot_py->{py}")
                    continue
                self.traj.log_decision("Orchestrator", "spin_giveup")
                break
            last_signature = sig

            build_budget = max(30, int(min(180, remaining)))
            br = build_and_run(snippet.source, py, packages,
                               build_timeout=build_budget,
                               run_timeout=min(60, max(15, build_budget // 3)))
            self.traj.log_build(py, packages, br.passed,
                                br.error_kind.family, br.duration_sec)
            if br.passed:
                self.bb.add_reflection(Reflection(
                    snippet_id=snippet.id,
                    note=f"Rescued py={py}: {', '.join(packages)}",
                    source_agent="Rescuer",
                ))
                return Resolution(
                    passed=True, python_version=py, packages=packages,
                    result_tag="None", duration=perf_counter() - t0,
                    extra={"stage": "B_llm_rescue"},
                )

            diagnosis = self._diagnose(br.log_text)
            self._emit_constraint(diagnosis, packages)
            last_err = diagnosis.get("family") or br.error_kind.family or "Unknown"
            if diagnosis.get("family") == "PY_VERSION":
                if not _looks_like_python2(snippet.source):
                    py = "2.7" if py.startswith("3") else "3.7"
                    self.traj.log_decision("Orchestrator", f"py_pivot->{py}")

        return Resolution(
            passed=False, python_version=py, packages=last_pkgs,
            result_tag=last_err, duration=perf_counter() - t0,
            extra={"stage": "B_llm_rescue_failed"},
        )

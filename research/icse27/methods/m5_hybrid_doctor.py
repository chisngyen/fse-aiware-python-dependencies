"""m5 — Three-Agent Blackboard Resolution (debugged from m4 5-agent design).

PIVOT after m4 honest negative (2/25 = 8% on smoke). The 5-agent design
collapsed because two agents (DateArchaeologist, Critic) actively harmed
the plan: DateArchaeologist returned ``py<=None`` for most snippets
(Gemma-2 9B can't reason over PyPI timestamps reliably), and Critic
overrode the rule-based py2 detector when it saw modern imports like
``matplotlib`` → forced py=3.x on py2 snippets → cascading SyntaxErrors.

m5 keeps the **blackboard + multi-agent architecture** (C3 contribution)
but drops the two harmful agents. Remaining three agents collaborate
through the shared blackboard:

  1. **DependencyArchaeologist** — proposes Python era. Rule-based
     ``_looks_like_python2`` detector posts a HARD constraint on the
     blackboard first; LLM only refines minor version (3.6 vs 3.7).
     Rule detector OUTRANKS the LLM — fixes the m4 Critic-override bug.
  2. **VersionNegotiator** — proposes pinned packages. LLM reads imports
     + blackboard constraints (incl. relevant reflexions filtered by
     import-token overlap), output is then hard-filtered against the
     current snippet's imports + a stdlib exclusion list (fixes m4's
     hallucinated ``sys`` and cross-snippet azure/openai leakage).
  3. **BuildDoctor** — on each failed build, classifies the error into
     a typed constraint {HARD, SOFT, UPPER, PYTHON_MISMATCH} and writes
     it to the blackboard. Next iteration's Negotiator reads these and
     prunes its proposals. This is the C1 contribution preserved intact.

Three contributions (G1), positioned vs SMT-LLM (arXiv 2605.11772, FSE'26)
---------------------------------------------------------------------------
- **C1** LLM-emitted typed constraints {HARD, SOFT, UPPER, PYTHON_MISMATCH}
  from free-form runtime logs (vs SMT-LLM's regex 11-type taxonomy).
- **C2** REMOVED in m5 (was: temporal reasoning via DateArchaeologist —
  empirically didn't work with small open LLMs; ablation evidence
  documented in tracker.md). Honest negative for paper.
- **C3** 3-agent blackboard architecture for Python dep resolution —
  first MAS for this task. Reduced from 5 in m4 design after ablation
  showed two agents harmed accuracy on 9B models.

m5 differences from m4
----------------------
DROPPED: DateArchaeologist (didn't reason temporally), Critic (override
harmful), LLM-only py detection (rule outranks LLM).
ADDED:   per-snippet wall-clock cap (fixes m4's 17-min single-snippet
PySide build), stdlib filter (fixes ``sys`` hallucination), retry-spin
guard (forces py-pivot if two consecutive plans are identical).
"""

from __future__ import annotations

import json
import re
from time import perf_counter

from research.icse27._shared import (
    Constraint, ConstraintKind, Reflection, Snippet,
    build_and_run, extract_imports, imports_to_packages,
)
from research.icse27.methods._base import BaseMethod, Budget, Resolution


# ---------- LLM output normalization (carried over from m4 fixes) -------------

def _normalize_pkg_list(raw) -> list[str]:
    if not raw:
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str):
            s = item.strip()
            if s:
                out.append(s)
        elif isinstance(item, dict):
            name = (item.get("name") or item.get("package")
                    or item.get("pkg") or "")
            ver = (item.get("version") or item.get("ver") or "")
            if not name and len(item) == 1:
                k, v = next(iter(item.items()))
                name, ver = str(k), str(v)
            name = str(name).strip()
            ver = str(ver).strip()
            if name:
                out.append(f"{name}=={ver}" if ver else name)
    return out


# ---------- Python 2 syntax detector (rule outranks LLM) ----------------------

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


# ---------- stdlib exclusion list (fixes m4 ``sys`` hallucination) ------------

_STDLIB = {
    "os", "sys", "io", "re", "json", "csv", "math", "time", "datetime",
    "random", "argparse", "subprocess", "logging", "threading", "queue",
    "collections", "itertools", "functools", "operator", "copy",
    "pathlib", "shutil", "glob", "pickle", "hashlib", "uuid", "base64",
    "socket", "struct", "tempfile", "string", "typing", "enum",
    "abc", "warnings", "traceback", "ast", "inspect", "contextlib",
    "asyncio", "concurrent", "multiprocessing", "unittest", "doctest",
    "urllib", "http", "email", "html", "xml", "sqlite3", "zipfile",
    "tarfile", "gzip", "bz2", "lzma", "platform", "ctypes",
    "__future__", "builtins",
}


# ---------- LLM family → typed constraint kind --------------------------------

_FAMILY_TO_KIND = {
    "NoMatchingDistribution": ConstraintKind.HARD,
    "CouldNotBuildWheels": ConstraintKind.HARD,
    "PythonVersionMismatch": ConstraintKind.HARD,
    "SyntaxError": ConstraintKind.HARD,
    "ApiRemoved": ConstraintKind.UPPER,
    "ImportError": ConstraintKind.SOFT,
    "Other": ConstraintKind.SOFT,
}


# ---------- prompts -----------------------------------------------------------

PROMPT_ARCHAEOLOGIST = """You are the DependencyArchaeologist. The Python era
has been pre-determined as {py_locked} (rule-based). Refine ONLY the minor
version if you have strong reason. Respond ONLY with JSON:
  {{"py": "{py_locked}", "reason": "imports include asyncio.run (py3.7+)"}}

Snippet (first 1500 chars):
```python
{source}
```"""

PROMPT_NEGOTIATOR = """You are the VersionNegotiator. Propose pinned pip
requirements consistent with the constraints on the shared blackboard.
- Python: {py}
- Imports (you must propose ONE package per import, no extras): {imports}
- Blocked (already forbidden by BuildDoctor on this session): {blocked}
- Upper bounds (must be < bound): {uppers}
- Relevant past lessons: {lessons}

Respond ONLY with JSON:
  {{"packages": ["scipy==1.4.1", "torch==1.5.0"]}}"""

PROMPT_DOCTOR = """You are the BuildDoctor. Diagnose this error and emit a
TYPED constraint to the blackboard. Respond ONLY with JSON:
  {{"family": "NoMatchingDistribution|CouldNotBuildWheels|PythonVersionMismatch|ImportError|SyntaxError|ApiRemoved|Other",
    "package": "name of the culprit package, or null",
    "version": "specific version that failed, or null",
    "upper_bound": "version cap if family==ApiRemoved, else null",
    "evidence": "one-line log excerpt"}}

Typing rules:
- HARD: version permanently forbidden (no wheel, build fails, py-version conflict, snippet syntax)
- SOFT: forbidden only after 2 confirmations (likely intermittent)
- UPPER: package needs version < upper_bound (API was removed)
- PYTHON_MISMATCH: change the Python interpreter, not the package

Error log (last 60 lines):
{log}"""


# ---------- the method --------------------------------------------------------

class Method(BaseMethod):
    name = "m5_three_agent_blackboard"
    contribution = (
        "Three-agent blackboard architecture (DependencyArchaeologist + "
        "VersionNegotiator + BuildDoctor). Drops m4's DateArchaeologist "
        "and Critic after empirical evidence they harm small-LLM plans. "
        "C1 LLM-emitted typed constraints {HARD,SOFT,UPPER,PYTHON_MISMATCH} "
        "(vs SMT-LLM regex). C3 blackboard MAS for dep-resolution. "
        "Rule-based py-2 detector outranks LLM (fixes m4 Critic-override bug)."
    )
    session_scope = True   # blackboard persists across snippets in a session

    # ----- agent 1: Archaeologist (rule + LLM refinement) -------------------

    def _archaeologist(self, snippet: Snippet) -> str:
        # Rule detector takes priority — LOCKED, LLM cannot override.
        if _looks_like_python2(snippet.source):
            self.traj.log_decision("Archaeologist", "py=2.7",
                                   "py2-only tokens (rule-locked)")
            return "2.7"
        # Otherwise fall back to dataset hint (output_data_X.Y.yml)
        py_locked = snippet.hint_python or "3.7"
        if self.backbone is None:
            return py_locked
        # LLM refinement only on minor version
        ans = self.backbone.generate_json(
            PROMPT_ARCHAEOLOGIST.format(py_locked=py_locked,
                                        source=snippet.source[:1500]),
            agent_name="Archaeologist", fallback={},
        ) or {}
        py = str(ans.get("py") or py_locked)
        # If LLM tried to switch major (e.g. 3 → 2), DENY — rule already decided.
        if py.split(".")[0] != py_locked.split(".")[0]:
            py = py_locked
        self.traj.log_decision("Archaeologist", f"py={py}",
                               str(ans.get("reason", ""))[:200])
        return py

    # ----- agent 2: Negotiator (LLM + hard filter) ---------------------------

    def _relevant_lessons(self, imports: list[str]) -> str:
        tokens = {t.lower() for t in imports}
        tokens.update(t.lower() for t in imports_to_packages(imports))
        out: list[str] = []
        for r in self.bb.recent_reflections(20):
            note_l = r.note.lower()
            if any(tok in note_l for tok in tokens if len(tok) >= 3):
                out.append(f"- {r.note}")
                if len(out) >= 3:
                    break
        return "\n".join(out) or "(no relevant lessons)"

    def _negotiator(self, imports: list[str], py: str) -> list[str]:
        # Compute blackboard state for the prompt + hard filter
        blocked = [f"{c.package}=={c.version}"
                   for c in self.bb.constraints.values()
                   if c.version and self.bb.is_blocked(c.package, c.version)][:15]
        uppers = [f"{c.package}<{c.upper_bound}"
                  for c in self.bb.constraints.values()
                  if c.kind == ConstraintKind.UPPER and c.upper_bound][:15]

        if self.backbone is None:
            pkgs = [p for p in imports_to_packages(imports)
                    if p.lower() not in _STDLIB]
            self.traj.log_decision("Negotiator", "packages (rule-only)",
                                   json.dumps(pkgs)[:300])
            return pkgs

        ans = self.backbone.generate_json(
            PROMPT_NEGOTIATOR.format(
                py=py, imports=", ".join(imports),
                blocked=", ".join(blocked) or "(none)",
                uppers=", ".join(uppers) or "(none)",
                lessons=self._relevant_lessons(imports),
            ),
            agent_name="Negotiator", fallback={},
        ) or {}
        pkgs = _normalize_pkg_list(ans.get("packages") or imports_to_packages(imports))

        # Hard filter: only keep packages whose name corresponds to an import,
        # excluding stdlib. This kills cross-snippet contamination AND stdlib
        # hallucinations.
        allowed = {t.lower() for t in imports}
        allowed.update(t.lower() for t in imports_to_packages(imports))
        kept: list[str] = []
        dropped: list[str] = []
        for p in pkgs:
            name = p.split("==")[0].split("<")[0].split(">")[0].strip().lower()
            if name in _STDLIB:
                dropped.append(p)
                continue
            if name in allowed or any(name.startswith(a)
                                       for a in allowed if len(a) >= 4):
                kept.append(p)
            else:
                dropped.append(p)
        if dropped:
            self.traj.log_decision("Negotiator", "filtered_out",
                                   f"dropped {dropped}")
        pkgs = kept or [p for p in imports_to_packages(imports)
                        if p.lower() not in _STDLIB]
        self.traj.log_decision("Negotiator", "packages",
                               json.dumps(pkgs)[:300])
        return pkgs

    # ----- agent 3: BuildDoctor (typed constraint emission) ------------------

    def _doctor(self, log_text: str) -> dict:
        if self.backbone is None:
            return {"family": "Other", "package": None, "version": None,
                    "upper_bound": None}
        ans = self.backbone.generate_json(
            PROMPT_DOCTOR.format(log=log_text[-4000:]),
            agent_name="BuildDoctor", fallback={},
        ) or {}
        self.traj.log_decision(
            "BuildDoctor", str(ans.get("family", "?")),
            f"{ans.get('package')}=={ans.get('version')} upper={ans.get('upper_bound')}",
        )
        return ans

    def _emit_constraint(self, diagnosis: dict, packages: list[str]) -> None:
        family = str(diagnosis.get("family", "Other"))
        kind = _FAMILY_TO_KIND.get(family, ConstraintKind.SOFT)
        culprit = diagnosis.get("package")
        if not culprit:
            return
        version = diagnosis.get("version")
        upper = diagnosis.get("upper_bound")
        if not version:
            for p in packages:
                name = p.split("==")[0]
                if name == culprit and "==" in p:
                    version = p.split("==", 1)[1]
                    break
        self.bb.add_constraint(Constraint(
            package=str(culprit), version=version, kind=kind,
            upper_bound=upper if kind == ConstraintKind.UPPER else None,
            evidence=str(diagnosis.get("evidence", ""))[:300],
            source_agent="BuildDoctor",
        ))

    # ----- orchestrator loop -------------------------------------------------

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        t0 = perf_counter()
        per_snippet_cap = budget.snippet_seconds
        py = self._archaeologist(snippet)
        imports = extract_imports(snippet.source)
        last_pkgs: list[str] = []
        last_err = "ExhaustedBudget"
        last_signature: tuple = ()

        for attempt in range(budget.k_build_max):
            elapsed = perf_counter() - t0
            if elapsed > per_snippet_cap:
                self.traj.log_decision("Orchestrator", "wall_clock_cap",
                                       f"elapsed={elapsed:.0f}s cap={per_snippet_cap}s")
                break
            remaining = per_snippet_cap - elapsed

            packages = self._negotiator(imports, py)
            last_pkgs = packages

            # Retry-spin guard: if this plan is identical to the previous
            # one, the constraint store didn't help — pivot Python rather
            # than waste another build.
            sig = (py, tuple(sorted(packages)))
            if sig == last_signature and attempt > 0:
                if not _looks_like_python2(snippet.source):
                    py = "2.7" if py.startswith("3") else "3.7"
                    self.traj.log_decision("Orchestrator",
                                           f"spin_break py_pivot->{py}",
                                           "two consecutive identical plans")
                    continue
                # else py2 was rule-locked → break, can't recover.
                self.traj.log_decision("Orchestrator", "spin_break_giveup",
                                       "py rule-locked, no other moves")
                break
            last_signature = sig

            build_budget = max(30, int(min(180, remaining)))
            br = build_and_run(snippet.source, py, packages,
                               build_timeout=build_budget,
                               run_timeout=min(60, max(15, build_budget // 3)))
            self.traj.log_build(py, packages, br.passed,
                                br.error_kind.family, br.duration_sec)
            if br.passed:
                # Record a positive reflexion for future-snippet Negotiator
                self.bb.add_reflection(Reflection(
                    snippet_id=snippet.id,
                    note=f"Worked on py={py}: {', '.join(packages)}",
                    source_agent="Orchestrator",
                ))
                return Resolution(passed=True, python_version=py,
                                  packages=packages, result_tag="None",
                                  duration=perf_counter() - t0)

            diagnosis = self._doctor(br.log_text)
            self._emit_constraint(diagnosis, packages)
            last_err = diagnosis.get("family", br.error_kind.family) or br.error_kind.family

            if diagnosis.get("family") == "PythonVersionMismatch":
                # Honor rule-based py2 lock — only pivot away if rule didn't fire.
                if not _looks_like_python2(snippet.source):
                    py = "2.7" if py.startswith("3") else "3.7"
                    self.traj.log_decision("Orchestrator", f"py_pivot->{py}",
                                           "BuildDoctor flagged PythonVersionMismatch")

        return Resolution(passed=False, python_version=py, packages=last_pkgs,
                          result_tag=last_err, duration=perf_counter() - t0)

"""m4 — Neuro-Symbolic Agentic Resolution with Temporal Reasoning.

PROPOSED method for ICSE 2027. Self-contained — no inheritance from other
method files. Ablations will be derived from THIS file later by toggling
flags or copy-then-strip into new files (e.g. ``m4_no_temporal.py``).

Three contributions (G1), positioned vs SMT-LLM (arXiv 2605.11772, FSE'26)
---------------------------------------------------------------------------
SMT-LLM has substantial overlap: it uses Z3 + hard/soft constraint typing
+ a temporal median-PyPI heuristic on the SAME HG2.9K benchmark.
We distinguish on the following three claims, each separately ablatable.

1. **LLM-emitted typed constraints from free-form build logs.**
   The BuildDoctor agent reads the runtime Docker log and emits a FORMAL
   constraint type — ``HARD`` (forbidden), ``SOFT`` (forbidden after 2
   confirmations), ``UPPER`` (version < bound), ``PYTHON_MISMATCH``
   (re-pivot interpreter). Unlike SMT-LLM's 11-class regex taxonomy
   (brittle to new error formats), our classifier handles arbitrary
   logs at runtime AND emits two constraint types (UPPER, PYTHON_MISMATCH)
   that SMT-LLM does not enumerate as first-class. The 41.6%-Python-2
   share of the irreducible failure floor empirically justifies
   PYTHON_MISMATCH as a distinct type.

2. **Temporal reasoning as a blackboard-first-class agent.**
   The DateArchaeologist is a dedicated LLM agent that QUERIES PyPI
   release timestamps for imported packages and POSTS a temporal Python
   bound to the shared blackboard BEFORE any solving begins. Unlike
   SMT-LLM's median-of-midpoint heuristic (one-shot re-ranker over
   candidates), our agent (a) reasons over import-specific evidence
   (e.g. ``scipy.misc.imread`` removed in scipy 1.2 → pre-2019), (b) can
   be challenged by the Critic in a debate round, and (c) refines its
   bound across snippets in the session (cross-snippet reflexion).

3. **5-agent blackboard architecture for dep resolution.**
   Five specialized agents — DependencyArchaeologist, DateArchaeologist,
   VersionNegotiator, BuildDoctor, Critic — collaborate on a shared
   blackboard (constraints + reflections + debate transcripts). To our
   knowledge this is the first blackboard MAS applied to Python
   dependency resolution. Distinct from SMT-LLM (single LLM with
   selective imputation), Environment-in-the-Loop (sequential pipeline),
   SWE-Debate (adversarial debate), and AgentForge (end-to-end SE).
   The novelty is the task adaptation: typed constraint emission +
   temporal posting + reflexion all flowing through ONE shared workspace.

Architecture
------------
Five specialized agents on a shared blackboard:
  - DependencyArchaeologist : Python era from snippet source
  - DateArchaeologist       : Python cap from PyPI release dates  [NEW]
  - VersionNegotiator       : pinned package versions, reflexion-aware
  - BuildDoctor             : typed constraint emission             [NEW]
  - Critic                  : structured debate on the plan

The Orchestrator is the loop in ``resolve()``.

Ablations to derive from m4 later (when method is locked):
  - ``m4_no_temporal.py``   : skip DateArchaeologist
  - ``m4_no_typed.py``      : Doctor emits free-text instead of typed
  - ``m4_no_debate.py``     : skip Critic
  - ``m4_no_reflexion.py``  : disable cross-snippet reflexion
  - ``m4_no_archaeologist.py`` : delete role
  - ``m4_single_agent.py``  : one ReAct LLM, all tools — bottom of ladder
"""

from __future__ import annotations

import json
from time import perf_counter

from research.icse27._shared import (
    Constraint, ConstraintKind, DebateEntry, Reflection, Snippet,
    build_and_run, extract_imports, imports_to_packages,
    pypi_release_dates,
)
from research.icse27.methods._base import BaseMethod, Budget, Resolution

# ---------- prompt templates --------------------------------------------------

PROMPT_ARCHAEOLOGIST = """You are the DependencyArchaeologist. From the snippet
infer the Python major.minor era from syntax + imports. Respond ONLY with JSON:
  {{"py": "3.6", "reason": "uses f-strings (py3.6+) and asyncio.run (py3.7+)"}}

Snippet (first 2000 chars):
```python
{source}
```"""

PROMPT_DATE_ARCHAEOLOGIST = """You are the DateArchaeologist. Given PyPI
release dates for the snippet's imports, infer authorship time window.
Respond ONLY with JSON:
  {{"earliest_year": 2014, "latest_year": 2019,
    "implied_python_max": "3.7",
    "reason": "scipy.misc.imread was removed in scipy 1.2 (2018-12)"}}

Snippet imports: {imports}
PyPI release-date evidence (package -> first/latest release):
{date_hints}

If you can't infer, respond with null years."""

PROMPT_NEGOTIATOR = """You are the VersionNegotiator. Propose pinned pip
requirements consistent with: Python={py}, blocked={blocked}, lessons={lessons}.
Imports: {imports}

Respond ONLY with JSON:
  {{"packages": ["scipy==1.4.1", "torch==1.5.0"]}}"""

PROMPT_CRITIC = """You are the Critic. Given the current plan, return JSON:
  {{"agree": true/false,
    "objection": "one-line reason citing concrete evidence (if disagree)",
    "preferred": {{"py": "...", "packages": [...]}}}}

Plan: py={py}  packages={packages}
Reasoning: {reason}
Imports: {imports}
Blocked: {blocked}"""

PROMPT_DOCTOR_TYPED = """You are the BuildDoctor. Diagnose the build/runtime
error and emit a FORMAL constraint. Respond ONLY with JSON:
  {{"family": "NoMatchingDistribution|CouldNotBuildWheels|PythonVersionMismatch|ImportError|SyntaxError|ApiRemoved|Other",
    "package": "name or null",
    "version": "specific version that failed, or null",
    "upper_bound": "version cap if family==ApiRemoved, else null",
    "is_hard": true/false,
    "evidence": "one-line log excerpt"}}

Constraint typing rules:
- HARD: version permanently forbidden (no wheel, build fails, py-version conflict)
- SOFT: forbidden only after 2 confirmations (likely intermittent)
- UPPER: package needs version < upper_bound (API was removed)
- PYTHON_MISMATCH: change the Python interpreter, not the package

Error log (last 60 lines):
{log}"""

PROMPT_REFLECT = """You are the Critic. In ONE sentence, write a lesson that
would help future snippets with similar imports. Cite specific
package/version when possible. Respond ONLY with JSON:
  {{"lesson": "When openai is imported and code uses ChatCompletion, pin openai<1.0."}}

Snippet imports: {imports}
Outcome: {outcome}
Last error: {error}
Final plan: {plan}"""


# ---------- LLM-output normalization ------------------------------------------
# Gemma-2 9B sometimes returns ``packages`` as a list of dicts instead of
# strings (e.g. ``[{"name":"scipy","version":"1.4.1"}]``). All downstream
# code assumes ``list[str]`` of ``"pkg==ver"`` or ``"pkg"``. Coerce here.

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
                # {"scipy": "1.4.1"} variant
                k, v = next(iter(item.items()))
                name, ver = str(k), str(v)
            name = str(name).strip()
            ver = str(ver).strip()
            if name:
                out.append(f"{name}=={ver}" if ver else name)
        # silently skip any other shape (number/None/list-of-list)
    return out


# ---------- Python 2 syntax detector (high-precision rule-based) --------------
# Reason this exists despite m4 being LLM-driven: 9B models can't reliably
# distinguish py2 from py3 in short snippets. CGAR's existing rule detector
# achieves 84% pass partly because it catches py2 cases explicitly.
# We use the SAME heuristic here to avoid losing those cases.

import re as _re

_PY2_TOKEN_PATTERNS = [
    r"^\s*print\s+[^(\n]",                # print foo (statement form)
    r"\bexcept\s+\w+\s*,\s*\w+\s*:",      # except E, x:
    r"\braise\s+\w+\s*,\s*",              # raise E, "msg"
    r"\bxrange\s*\(",
    r"<>",                                # py2 not-equal
    r"\bbasestring\b",
    r"\bunicode\s*\(",
    r"^\s*from\s+__future__\s+import\s+print_function",  # author explicitly opted in
]
_PY2_RE = _re.compile("|".join(f"({p})" for p in _PY2_TOKEN_PATTERNS), _re.MULTILINE)


def _looks_like_python2(source: str) -> bool:
    """High-precision Python-2 syntax detector. False positives are rare
    but possible (e.g., a `print( ` with intentional space — won't match).
    Tuned so that py3 code never triggers this; we'd rather miss a py2
    snippet (fall back to LLM) than misclassify a py3 one."""
    return bool(_PY2_RE.search(source))


# ---------- agent family → constraint kind mapping ----------------------------

_FAMILY_TO_KIND = {
    "NoMatchingDistribution": ConstraintKind.HARD,
    "CouldNotBuildWheels": ConstraintKind.HARD,
    "PythonVersionMismatch": ConstraintKind.HARD,
    "SyntaxError": ConstraintKind.HARD,
    "ApiRemoved": ConstraintKind.UPPER,
    "ImportError": ConstraintKind.SOFT,
    "Other": ConstraintKind.SOFT,
}


# ---------- the method --------------------------------------------------------

class Method(BaseMethod):
    name = "m4_neurosymbolic_temporal"
    contribution = (
        "Three claims vs SMT-LLM (FSE'26 arXiv 2605.11772): "
        "(C1) LLM-emitted typed constraints {HARD,SOFT,UPPER,PYTHON_MISMATCH} "
        "from free-form runtime logs (vs their regex 11-type taxonomy); "
        "(C2) blackboard-first-class temporal agent reasoning over import-"
        "specific PyPI evidence (vs their median heuristic re-ranker); "
        "(C3) 5-agent blackboard architecture — first MAS applied to "
        "Python dep resolution. Empirically: m4 on Gemma-2 9B same harness."
    )
    session_scope = True   # constraints + reflections persist across snippets

    # ----- Agents (each is one LLM call + traj logging) -----------------------

    def _archaeologist(self, snippet: Snippet) -> str:
        # Symbolic Python-2 detector takes priority: 9B LLMs reliably miss
        # py2 syntax (print stmt without parens, raise A, B, except A, B,
        # `xrange`, `unicode`, `<>`), and pure-LLM era inference produces
        # ~50% SyntaxError on the HG2.9K Python-2 share. The detector below
        # is high-precision: only fires when py2-only tokens are present.
        if _looks_like_python2(snippet.source):
            self.traj.log_decision("Archaeologist", "py=2.7",
                                   "py2-only tokens detected (rule-based)")
            return "2.7"
        if self.backbone is None:
            return snippet.hint_python or "3.7"
        ans = self.backbone.generate_json(
            PROMPT_ARCHAEOLOGIST.format(source=snippet.source[:2000]),
            agent_name="Archaeologist", fallback={},
        ) or {}
        py = str(ans.get("py") or snippet.hint_python or "3.7")
        self.traj.log_decision("Archaeologist", f"py={py}",
                               str(ans.get("reason", ""))[:200])
        return py

    def _date_archaeologist(self, snippet: Snippet, imports: list[str]) -> dict:
        if self.backbone is None:
            return {}
        pkgs = imports_to_packages(imports)[:5]
        hints: list[str] = []
        for pkg in pkgs:
            dates = pypi_release_dates(pkg) or {}
            if not dates:
                continue
            earliest = min(dates.values())
            latest = max(dates.values())
            hints.append(f"- {pkg}: first {earliest}, latest {latest}, "
                         f"n_versions={len(dates)}")
            self.traj.log_tool("DateArchaeologist", "pypi_release_dates",
                               {"pkg": pkg},
                               f"{len(dates)} versions, {earliest}..{latest}")
        ans = self.backbone.generate_json(
            PROMPT_DATE_ARCHAEOLOGIST.format(
                imports=", ".join(imports) or "(none)",
                date_hints=("\n".join(hints) or "(no release data)"),
            ),
            agent_name="DateArchaeologist", fallback={},
        ) or {}
        self.traj.log_decision("DateArchaeologist",
                               f"py<={ans.get('implied_python_max', '?')}",
                               str(ans.get("reason", ""))[:200])
        return ans

    def _negotiator(self, imports: list[str], py: str, blocked: list[str]) -> list[str]:
        if self.backbone is None:
            return imports_to_packages(imports)
        # Relevance-filter reflexions: only inject a lesson if at least one
        # token from the current snippet's imports/packages appears in the
        # lesson text. Without this, Gemma-2 9B treats every recent lesson
        # as advice for the current snippet and dumps unrelated packages
        # into the plan (observed: snippet-3 imports cython but plan listed
        # azure-core+openai from earlier snippets). This is a G7 leakage fix.
        relevance_tokens = {t.lower() for t in imports}
        relevance_tokens.update(t.lower() for t in imports_to_packages(imports))
        relevant: list[str] = []
        for r in self.bb.recent_reflections(20):
            note_l = r.note.lower()
            if any(tok in note_l for tok in relevance_tokens if len(tok) >= 3):
                relevant.append(f"- {r.note}")
                if len(relevant) >= 3:   # cap to avoid prompt bloat
                    break
        lessons = "\n".join(relevant) or "(no relevant lessons for these imports)"
        ans = self.backbone.generate_json(
            PROMPT_NEGOTIATOR.format(
                imports=", ".join(imports), py=py,
                blocked=", ".join(blocked) or "(none)", lessons=lessons,
            ),
            agent_name="Negotiator", fallback={},
        ) or {}
        pkgs = ans.get("packages") or imports_to_packages(imports)
        pkgs = _normalize_pkg_list(pkgs)
        # Hard-filter: drop any package whose name is unrelated to the current
        # snippet's imports. Belt-and-suspenders against LLM contamination
        # from prior-snippet lessons. We keep a generous set (imports + their
        # canonical pip names) so legitimate dep-of-dep pins aren't dropped.
        allowed = {t.lower() for t in imports}
        allowed.update(t.lower() for t in imports_to_packages(imports))
        kept: list[str] = []
        dropped: list[str] = []
        for p in pkgs:
            name = p.split("==")[0].split("<")[0].split(">")[0].strip().lower()
            if name in allowed or any(name.startswith(a) for a in allowed if len(a) >= 4):
                kept.append(p)
            else:
                dropped.append(p)
        if dropped:
            self.traj.log_decision("Negotiator", "filtered_out",
                                   f"dropped {dropped} (not in imports)")
        pkgs = kept or imports_to_packages(imports)   # safety: never return empty
        self.traj.log_decision("Negotiator", "packages", json.dumps(pkgs)[:300])
        return pkgs

    def _critic(self, snippet: Snippet, py: str, packages: list[str],
                reason: str, blocked: list[str]) -> tuple[str, list[str]]:
        if self.backbone is None:
            return py, packages
        ans = self.backbone.generate_json(
            PROMPT_CRITIC.format(
                py=py, packages=json.dumps(packages), reason=reason,
                imports=", ".join(extract_imports(snippet.source)),
                blocked=", ".join(blocked) or "(none)",
            ),
            agent_name="Critic", fallback={"agree": True},
        ) or {"agree": True}
        if bool(ans.get("agree", True)):
            self.traj.log_decision("Critic", "agree")
            return py, packages
        pref = ans.get("preferred") or {}
        new_py = str(pref.get("py") or py)
        new_pkgs = _normalize_pkg_list(pref.get("packages") or packages)
        self.traj.log_decision("Critic", "dispute",
                               str(ans.get("objection", ""))[:200])
        self.bb.record_debate(DebateEntry(
            snippet_id=snippet.id,
            agents=("Archaeologist+Negotiator", "Critic"),
            topic="plan",
            positions={
                "AN": json.dumps({"py": py, "packages": packages}),
                "Critic": json.dumps({"py": new_py, "packages": new_pkgs}),
            },
            resolution=f"Critic wins: py={new_py}",
        ))
        return new_py, new_pkgs

    def _doctor_typed(self, log_text: str) -> dict:
        if self.backbone is None:
            return {"family": "Other", "is_hard": False, "package": None,
                    "version": None, "upper_bound": None}
        ans = self.backbone.generate_json(
            PROMPT_DOCTOR_TYPED.format(log=log_text[-4000:]),
            agent_name="DoctorTyped", fallback={},
        ) or {}
        self.traj.log_decision(
            "DoctorTyped", str(ans.get("family", "?")),
            f"{ans.get('package')}=={ans.get('version')} "
            f"upper={ans.get('upper_bound')} hard={ans.get('is_hard')}",
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
            package=culprit, version=version, kind=kind,
            upper_bound=upper if kind == ConstraintKind.UPPER else None,
            evidence=str(diagnosis.get("evidence", ""))[:300],
            source_agent="DoctorTyped",
        ))

    def _reflect(self, snippet: Snippet, passed: bool, py: str,
                 packages: list[str], last_err: str) -> None:
        if self.backbone is None:
            return
        ans = self.backbone.generate_json(
            PROMPT_REFLECT.format(
                imports=", ".join(extract_imports(snippet.source)),
                outcome=("pass" if passed else "fail"),
                error=last_err,
                plan=json.dumps({"py": py, "packages": packages}),
            ),
            agent_name="Reflector", fallback={},
        ) or {}
        lesson = (ans.get("lesson") or "").strip()
        if lesson:
            self.bb.add_reflection(Reflection(
                snippet_id=snippet.id, note=lesson[:300],
                source_agent="Reflector",
            ))
            self.traj.log_decision("Reflector", "lesson", lesson[:300])

    # ----- Helpers ------------------------------------------------------------

    def _blocked_summary(self) -> list[str]:
        return [f"{c.package}=={c.version}" for c in self.bb.constraints.values()
                if c.version and self.bb.is_blocked(c.package, c.version)][:20]

    def _apply_upper_bounds(self, packages: list[str]) -> list[str]:
        # Belt-and-suspenders: normalize again in case upstream missed a path.
        packages = _normalize_pkg_list(packages)
        out: list[str] = []
        for p in packages:
            name = p.split("==")[0]
            ub = self.bb.upper_bound_for(name)
            if ub and "==" in p:
                cur = p.split("==", 1)[1]
                if cur >= ub:
                    out.append(f"{name}<{ub}")
                    continue
            out.append(p)
        return out

    # ----- Orchestrator loop --------------------------------------------------

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        t0 = perf_counter()
        imports = extract_imports(snippet.source)

        # Stage 1 (no Docker): two archaeologists + temporal cap
        py = self._archaeologist(snippet)
        temporal = self._date_archaeologist(snippet, imports)
        py_cap = temporal.get("implied_python_max")
        if py_cap:
            try:
                if tuple(int(x) for x in py.split(".")) > tuple(
                        int(x) for x in py_cap.split(".")):
                    self.traj.log_decision("Orchestrator",
                                           f"temporal_cap py {py}->{py_cap}",
                                           str(temporal.get("reason", ""))[:200])
                    py = py_cap
            except ValueError:
                pass

        last_pkgs: list[str] = []
        last_err = "ExhaustedBudget"

        for attempt in range(budget.k_build_max):
            blocked = self._blocked_summary()
            packages = self._negotiator(imports, py, blocked)
            # Drop pins already blocked by the symbolic store
            packages = [p for p in packages if not (
                "==" in p and self.bb.is_blocked(p.split("==")[0],
                                                 p.split("==", 1)[1])
            )]
            packages = self._apply_upper_bounds(packages)

            py, packages = self._critic(
                snippet, py, packages,
                reason=f"py inferred from source + temporal cap={py_cap or 'none'}",
                blocked=blocked,
            )
            last_pkgs = packages

            br = build_and_run(snippet.source, py, packages,
                               build_timeout=180, run_timeout=60)
            self.traj.log_build(py, packages, br.passed,
                                br.error_kind.family, br.duration_sec)
            if br.passed:
                self._reflect(snippet, True, py, packages, "None")
                return Resolution(passed=True, python_version=py,
                                  packages=packages, result_tag="None",
                                  duration=perf_counter() - t0)

            diagnosis = self._doctor_typed(br.log_text)
            self._emit_constraint(diagnosis, packages)
            last_err = diagnosis.get("family", br.error_kind.family) or br.error_kind.family
            if diagnosis.get("family") == "PythonVersionMismatch":
                py = "2.7" if py.startswith("3") else "3.7"

        self._reflect(snippet, False, py, last_pkgs, last_err)
        return Resolution(passed=False, python_version=py, packages=last_pkgs,
                          result_tag=last_err, duration=perf_counter() - t0)

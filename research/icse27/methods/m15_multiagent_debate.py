"""m15 — Multi-Agent Debate (flagship candidate for ICSE'27).

Four specialized LLM agents + Orchestrator + Blackboard. Each agent has a
narrow role, a prompt, and a tool subset. Debate is triggered when two
agents disagree on a package's pin; an arbiter resolves using evidence
(PyPI release dates, prior build logs) recorded on the blackboard.

Novelty claim
-------------
First multi-agent system with EXPLICIT debate/arbitration protocol for
Python dependency resolution. No rule-based constraint store (CGAR), no
historical-CSV replay (Oracle / m10): every decision is grounded in
live PyPI metadata + Docker verifier feedback + LLM reasoning.

R4 compliance: this file does NOT read pllm/memres/cgar result CSVs.
The only inputs are the snippet source, live PyPI, and Docker logs.

Verifier
--------
Hybrid:
  1. PyPI metadata + wheel_filter pre-check (cheap, no Docker)
  2. Docker build+run only when pre-check passes

This mirrors the design discussed in the planning conversation. Both gates
are needed: the pre-check eliminates obviously infeasible plans (saves
Docker time); Docker is the ground-truth verifier (saves correctness).
"""

from __future__ import annotations

import json
import re
from time import perf_counter
from typing import Any

from research.icse27._shared import (
    Blackboard, Constraint, ConstraintKind, DebateEntry, Reflection,
    LLMBackbone, Snippet, TrajectoryLogger,
    build_and_run, query_pypi, pypi_release_dates, wheel_filter,
    parse_docker_error, extract_imports, imports_to_packages,
)
from research.icse27.methods._base import BaseMethod, Budget, Resolution


# ============================================================================
# Prompts — single-field JSON, friendly to small LLMs (Gemma-2 9B, Qwen 7B…)
# ============================================================================

PROMPT_ARCHAEOLOGIST = """You are the DependencyArchaeologist agent. Read a
Python snippet and infer: (a) the most likely authorship era (year), (b) the
target Python version, (c) any deprecated API usage that hints at older
package versions.

Return ONLY a JSON object:
{{"era_year": <int 2010-2024>, "python_version": "<X.Y>", "deprecated_hints": [<string>...]}}

Imports detected: {imports}
Snippet (first 1200 chars):
```python
{source}
```
"""

PROMPT_NEGOTIATOR = """You are the VersionNegotiator agent. Given a list of
imports, an era estimate, and live PyPI metadata, propose a PINNED plan:
each package gets `pkg==version`. Prefer wheels available for the target
Python. Prefer versions released near the era year.

Return ONLY a JSON array of strings: ["pkg==1.2.3", ...]

Target Python: {python_version}
Era estimate: {era_year}
Imports: {imports}
PyPI evidence (versions sorted newest→oldest, top 8 per package):
{pypi_evidence}
Existing blackboard constraints (avoid these): {forbidden}
"""

PROMPT_DOCTOR = """You are the BuildDoctor agent. A Docker build/run just
FAILED for a candidate plan. Read the error and propose a counter-plan.

Plan that failed: {plan}
Python: {python_version}
Error family: {error_family}
Error detail: {error_detail}
Tail of build log (last 1500 chars):
{log_tail}

Return ONLY a JSON object:
{{"action": "<downgrade|upgrade|swap_pkg|add_pkg|drop_pkg|change_python>",
  "target_package": "<pkg or empty>",
  "new_version": "<version or empty>",
  "new_python": "<X.Y or empty>",
  "reasoning": "<one short sentence>"}}
"""

PROMPT_ARBITER = """You are the Arbiter. Two agents disagree on a package
pin. Decide which to use based on evidence below.

Package: {package}
Negotiator proposes: {pin_a}  (rationale: {rationale_a})
Doctor proposes:     {pin_b}  (rationale: {rationale_b})
Era estimate: {era_year}
Release dates near era: {release_dates}

Return ONLY a JSON object:
{{"winner": "<pin_a or pin_b>", "reason": "<one short sentence>"}}
"""


# ============================================================================
# Agent classes — each owns a prompt + a thin LLM wrapper
# ============================================================================

class _AgentBase:
    name: str = "agent"

    def __init__(self, backbone: LLMBackbone | None, traj: TrajectoryLogger) -> None:
        self.backbone = backbone
        self.traj = traj

    def _ask_json(self, prompt: str, fallback: Any) -> Any:
        if self.backbone is None:
            return fallback
        return self.backbone.generate_json(prompt, agent_name=self.name, fallback=fallback)

    def _log(self, snippet_id: str, event: str, payload: dict) -> None:
        self.traj.log(snippet_id, {"agent": self.name, "event": event, **payload})


class DependencyArchaeologist(_AgentBase):
    name = "archaeologist"

    def analyze(self, snippet: Snippet, imports: list[str]) -> dict:
        source = (snippet.source or "")[:1200]
        prompt = PROMPT_ARCHAEOLOGIST.format(imports=imports, source=source)
        fallback = {"era_year": 2020, "python_version": "3.8", "deprecated_hints": []}
        out = self._ask_json(prompt, fallback=fallback)
        if not isinstance(out, dict):
            out = fallback
        out.setdefault("era_year", 2020)
        out.setdefault("python_version", "3.8")
        out.setdefault("deprecated_hints", [])
        self._log(snippet.id, "analyze", out)
        return out


class VersionNegotiator(_AgentBase):
    name = "negotiator"

    def propose(self, snippet: Snippet, imports: list[str], era_year: int,
                python_version: str, bb: Blackboard) -> list[str]:
        evidence = _collect_pypi_evidence(imports, python_version, top_k=8)
        forbidden = sorted({f"{p}=={v}" for (p, v), c in bb.constraints.items()
                            if v and bb.is_blocked(p, v)})
        prompt = PROMPT_NEGOTIATOR.format(
            python_version=python_version, era_year=era_year,
            imports=imports, pypi_evidence=evidence,
            forbidden=forbidden if forbidden else "(none)",
        )
        out = self._ask_json(prompt, fallback=[])
        plan = _coerce_plan(out, imports)
        # Apply upper bounds learned on the blackboard
        plan = _apply_upper_bounds(plan, bb)
        self._log(snippet.id, "propose", {"plan": plan, "era_year": era_year})
        return plan


class BuildDoctor(_AgentBase):
    name = "doctor"

    def diagnose(self, snippet: Snippet, plan: list[str], python_version: str,
                 build_log: str, err_family: str, err_detail: str) -> dict:
        prompt = PROMPT_DOCTOR.format(
            plan=plan, python_version=python_version,
            error_family=err_family, error_detail=err_detail,
            log_tail=(build_log or "")[-1500:],
        )
        fallback = {"action": "downgrade", "target_package": "",
                    "new_version": "", "new_python": "", "reasoning": ""}
        out = self._ask_json(prompt, fallback=fallback)
        if not isinstance(out, dict):
            out = fallback
        self._log(snippet.id, "diagnose", out)
        return out


class Arbiter(_AgentBase):
    name = "arbiter"

    def decide(self, snippet: Snippet, package: str, pin_a: str, pin_b: str,
               rationale_a: str, rationale_b: str, era_year: int) -> str:
        dates = pypi_release_dates(package) or {}
        # Window: era ± 2 years
        window = {v: d for v, d in dates.items()
                  if d and abs(int(d[:4]) - era_year) <= 2}
        prompt = PROMPT_ARBITER.format(
            package=package, pin_a=pin_a, pin_b=pin_b,
            rationale_a=rationale_a, rationale_b=rationale_b,
            era_year=era_year, release_dates=dict(list(window.items())[:8]),
        )
        out = self._ask_json(prompt, fallback={"winner": pin_a, "reason": "fallback"})
        winner = out.get("winner") if isinstance(out, dict) else pin_a
        if winner not in (pin_a, pin_b):
            winner = pin_a
        self._log(snippet.id, "arbitrate",
                  {"package": package, "winner": winner,
                   "options": [pin_a, pin_b]})
        return winner


# ============================================================================
# ConstraintLibrarian — thin role: exposes blackboard reads, records writes
# ============================================================================

class ConstraintLibrarian:
    """Not an LLM agent. Owns reads/writes to the blackboard with type-safety
    so other agents don't accidentally bypass confirmation logic."""

    name = "librarian"

    def __init__(self, bb: Blackboard, traj: TrajectoryLogger) -> None:
        self.bb = bb
        self.traj = traj

    def record_failure(self, snippet_id: str, plan: list[str],
                       python_version: str, err) -> None:
        if err.package and err.is_hard:
            for pin in plan:
                pkg, ver = _split_pin(pin)
                if pkg == err.package:
                    self.bb.add_constraint(Constraint(
                        package=pkg, version=ver, kind=ConstraintKind.HARD,
                        python_version=python_version, evidence=err.detail,
                        source_agent="librarian",
                    ))
                    break
        elif err.package and not err.is_hard:
            for pin in plan:
                pkg, ver = _split_pin(pin)
                if pkg == err.package:
                    self.bb.add_constraint(Constraint(
                        package=pkg, version=ver, kind=ConstraintKind.SOFT,
                        python_version=python_version, evidence=err.detail,
                        source_agent="librarian",
                    ))
                    break
        # API-removed pattern: "cannot import name X from pkg" → upper bound
        m = re.search(r"cannot import name '?(\S+?)'?\s+from\s+'?(\S+?)'?",
                      err.detail or "")
        if m and err.package:
            self.bb.add_constraint(Constraint(
                package=err.package, version=None, kind=ConstraintKind.UPPER,
                upper_bound=_find_previous_version(err.package, _current_pin(plan, err.package)),
                evidence=err.detail, source_agent="librarian",
            ))
        self.traj.log(snippet_id, {"agent": "librarian", "event": "record",
                                   "constraint_summary": self.bb.summary()})


# ============================================================================
# Main Method
# ============================================================================

class Method(BaseMethod):
    name = "m15_multiagent_debate"
    contribution = (
        "Multi-agent debate (Archaeologist/Negotiator/Doctor/Librarian + Arbiter) "
        "with shared blackboard. No CSV replay, no rule-based constraint table — "
        "all decisions grounded in live PyPI + Docker feedback + LLM reasoning. "
        "Flagship novelty candidate for ICSE'27."
    )
    session_scope: bool = True  # blackboard persists across snippets in batch

    def __init__(self, backbone, blackboard, tools, config, trajectory):
        super().__init__(backbone, blackboard, tools, config, trajectory)
        self.archaeologist = DependencyArchaeologist(backbone, trajectory)
        self.negotiator = VersionNegotiator(backbone, trajectory)
        self.doctor = BuildDoctor(backbone, trajectory)
        self.arbiter = Arbiter(backbone, trajectory)
        self.librarian = ConstraintLibrarian(blackboard, trajectory)

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        t0 = perf_counter()
        source = snippet.source or ""
        imports = sorted(set(extract_imports(source)) - {""})
        py_pkgs_guess = imports_to_packages(imports)

        # === Stage 1: Archaeologist sets era + python version ===
        arch = self.archaeologist.analyze(snippet, imports)
        python_version = _normalize_py(arch.get("python_version", "3.8"))
        era_year = int(arch.get("era_year", 2020) or 2020)

        # === Stage 2: Negotiator proposes initial plan ===
        plan = self.negotiator.propose(snippet, py_pkgs_guess,
                                       era_year, python_version, self.bb)
        if not plan:
            plan = [f"{p}" for p in py_pkgs_guess]

        last_err_family = "Unknown"
        last_err_detail = ""
        # === Stage 3: Hybrid verifier loop ===
        for attempt in range(budget.k_build_max):
            if (perf_counter() - t0) > budget.snippet_seconds:
                break

            # (3a) Cheap PyPI pre-check
            ok, why = _pypi_pre_check(plan, python_version)
            if not ok:
                self.traj.log(snippet.id, {"agent": "orchestrator",
                                           "event": "pre_check_fail",
                                           "reason": why, "plan": plan})
                # Treat pre-check failure as a soft signal for Doctor
                doc = self.doctor.diagnose(snippet, plan, python_version,
                                            build_log=f"PyPI pre-check failed: {why}",
                                            err_family="PreCheck",
                                            err_detail=why)
                plan, python_version = _apply_doctor(plan, python_version, doc,
                                                     self.arbiter, snippet, era_year)
                continue

            # (3b) Docker build+run (ground truth)
            br = build_and_run(source, python_version, plan)
            self.traj.log(snippet.id, {"agent": "orchestrator",
                                       "event": "verify",
                                       "attempt": attempt,
                                       "passed": br.passed,
                                       "duration": br.duration_sec,
                                       "error_family": br.error_kind.family})
            if br.passed:
                return Resolution(
                    passed=True, python_version=python_version,
                    packages=plan, result_tag="None",
                    duration=perf_counter() - t0,
                    extra={"attempts": attempt + 1,
                           "era_year": era_year,
                           "bb_summary": self.bb.summary()},
                )

            # (3c) Record failure constraint
            self.librarian.record_failure(snippet.id, plan, python_version, br.error_kind)
            last_err_family = br.error_kind.family
            last_err_detail = br.error_kind.detail

            # (3d) Doctor diagnoses, optional debate vs Negotiator
            doc = self.doctor.diagnose(snippet, plan, python_version,
                                       br.log_text, br.error_kind.family,
                                       br.error_kind.detail)
            plan, python_version = _apply_doctor(plan, python_version, doc,
                                                 self.arbiter, snippet, era_year)

        # Failed within budget
        self.bb.add_reflection(Reflection(
            snippet_id=snippet.id,
            note=f"unsolved after {budget.k_build_max} attempts; last={last_err_family}",
            source_agent="orchestrator",
        ))
        return Resolution(
            passed=False, python_version=python_version,
            packages=plan, result_tag=last_err_family,
            duration=perf_counter() - t0,
            extra={"last_err_detail": last_err_detail,
                   "bb_summary": self.bb.summary()},
        )


# ============================================================================
# Helpers — pure, no LLM
# ============================================================================

def _split_pin(spec: str) -> tuple[str, str]:
    if "==" in spec:
        n, v = spec.split("==", 1)
        return n.strip(), v.strip()
    return spec.strip(), ""


def _current_pin(plan: list[str], package: str) -> str:
    for s in plan:
        n, v = _split_pin(s)
        if n == package:
            return v
    return ""


def _coerce_plan(out: Any, imports_fallback: list[str]) -> list[str]:
    if isinstance(out, list):
        return [str(s) for s in out if isinstance(s, (str, int, float))]
    if isinstance(out, dict) and "packages" in out:
        v = out["packages"]
        if isinstance(v, list):
            return [str(s) for s in v]
    return list(imports_fallback)


def _normalize_py(py: str) -> str:
    m = re.match(r"(\d+)\.(\d+)", str(py))
    return f"{m.group(1)}.{m.group(2)}" if m else "3.8"


def _apply_upper_bounds(plan: list[str], bb: Blackboard) -> list[str]:
    out: list[str] = []
    for spec in plan:
        pkg, ver = _split_pin(spec)
        ub = bb.upper_bound_for(pkg)
        if ub and ver:
            # If pin >= upper_bound → lower it to a version just below
            new_ver = _find_previous_version(pkg, ub) if _ver_ge(ver, ub) else ver
            out.append(f"{pkg}=={new_ver}" if new_ver else pkg)
        else:
            out.append(spec)
    return out


def _ver_ge(a: str, b: str) -> bool:
    def k(v: str) -> tuple:
        return tuple(int(x) if x.isdigit() else 0
                     for x in re.split(r"[.\-+]", v)[:4])
    try:
        return k(a) >= k(b)
    except Exception:  # noqa: BLE001
        return False


def _find_previous_version(package: str, upper: str) -> str:
    meta = query_pypi(package)
    if meta is None:
        return ""
    for v in meta.versions:  # newest first
        if not _ver_ge(v, upper) and v != upper:
            return v
    return ""


def _collect_pypi_evidence(packages: list[str], python_version: str,
                           top_k: int = 8) -> dict:
    out: dict = {}
    for p in packages[:20]:
        meta = query_pypi(p)
        if meta is None:
            out[p] = "[unavailable]"
            continue
        vers = [v for v in meta.versions
                if wheel_filter(meta, v, python_version)][:top_k]
        out[p] = vers or meta.versions[:top_k]
    return out


def _pypi_pre_check(plan: list[str], python_version: str) -> tuple[bool, str]:
    """Cheap feasibility filter: every pin must have a wheel for the target Python."""
    for spec in plan:
        pkg, ver = _split_pin(spec)
        if not pkg:
            continue
        meta = query_pypi(pkg)
        if meta is None:
            continue  # unknown, give it a chance
        if ver and ver not in meta.versions:
            return False, f"{pkg}=={ver} not on PyPI"
        if ver and not wheel_filter(meta, ver, python_version):
            return False, f"{pkg}=={ver} has no wheel for Python {python_version}"
    return True, ""


def _apply_doctor(plan: list[str], python_version: str, doc: dict,
                  arbiter: Arbiter, snippet: Snippet,
                  era_year: int) -> tuple[list[str], str]:
    """Apply Doctor's proposal; optionally arbitrate against the existing pin."""
    action = (doc.get("action") or "").lower()
    target = doc.get("target_package") or ""
    new_ver = doc.get("new_version") or ""
    new_py = doc.get("new_python") or ""
    rationale = doc.get("reasoning") or ""

    if action == "change_python" and new_py:
        return plan, _normalize_py(new_py)

    if not target:
        return plan, python_version

    # Locate current pin for target
    idx = -1
    old_pin = ""
    for i, spec in enumerate(plan):
        if _split_pin(spec)[0] == target:
            idx, old_pin = i, spec
            break

    if action == "drop_pkg" and idx >= 0:
        plan.pop(idx)
        return plan, python_version

    if action in ("downgrade", "upgrade", "swap_pkg") and new_ver:
        new_pin = f"{target}=={new_ver}"
        if idx >= 0 and old_pin and old_pin != new_pin and "==" in old_pin:
            # Disagreement → arbitrate
            winner = arbiter.decide(
                snippet, target, old_pin, new_pin,
                rationale_a="negotiator-proposed pin",
                rationale_b=rationale or "doctor-proposed pin",
                era_year=era_year,
            )
            plan[idx] = winner
        elif idx >= 0:
            plan[idx] = new_pin
        else:
            plan.append(new_pin)
        return plan, python_version

    if action == "add_pkg" and target:
        plan.append(f"{target}=={new_ver}" if new_ver else target)
        return plan, python_version

    return plan, python_version

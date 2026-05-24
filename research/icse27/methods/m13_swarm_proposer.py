"""m13 — Swarm Proposer with Diverse Stylized Agents.

Five independent LLM proposer agents, each with a DIFFERENT prompting
strategy:
  - ProposerA (newest stable, py3.10)
  - ProposerB (era 2018, py3.6/3.7)
  - ProposerC (conservative ranges, snippet-hinted py)
  - ProposerD (py3.6 wheels only)
  - ProposerE (py2.7 fallback)

Diversity-by-prompt = ensemble-of-experts pattern. Verifier (Docker)
tries the 5 plans deterministically.

Empirical (smoke n=50): 88% = m10. Genuine swarm rescues: 0/6 floor
cases. Distinct from m11 (synthesis) and m12 (mutation of existing).
"""

from __future__ import annotations

import json
import re
from time import perf_counter

from research.icse27._shared import (
    Snippet, build_and_run, extract_imports, imports_to_packages,
    ResolverIndexes, cascade_replay, looks_like_python2,
    csv_passed, packages_of, py_of, parse_plan_array,
)
from research.icse27.methods._base import BaseMethod, Budget, Resolution


def _imports_str(imports: list[str]) -> str:
    return ", ".join(imports) or "(none)"


PROMPTS = {
    "ProposerA_newest": """You are ProposerA — the "newest stable" agent.
The 3 standard resolvers failed. Propose a plan using the NEWEST STABLE
versions on PyPI for each imported package. Python should be 3.10.
Respond ONLY with a JSON array of "pkg==ver" strings.

Imports: {imports}""",

    "ProposerB_era2018": """You are ProposerB — the "era-2018" agent.
The 3 standard resolvers failed. The snippet was likely written
2017-2019. Propose pinned versions that were CURRENT in 2018.
Python should be 3.6 or 3.7.
Respond ONLY with a JSON array of "pkg==ver" strings.

Imports: {imports}""",

    "ProposerC_conservative": """You are ProposerC — the "conservative
ranges" agent. The 3 standard resolvers failed because of strict pins.
Use loose ranges (>=, <) instead of strict ==.
Respond ONLY with a JSON array of "pkg>=ver" strings.

Imports: {imports}
Python: {py}""",

    "ProposerD_py36": """You are ProposerD — the "Python 3.6 wheels" agent.
The 3 standard resolvers failed. Force Python 3.6 (most common wheel
target). Pick package versions that have manylinux py36 wheels.
Respond ONLY with a JSON array of "pkg==ver" strings.

Imports: {imports}""",

    "ProposerE_py27": """You are ProposerE — the "Python 2.7 fallback" agent.
The 3 standard resolvers failed. This might be a legacy Python 2 snippet.
Propose Python 2.7-compatible versions.
Respond ONLY with a JSON array of "pkg==ver" strings.

Imports: {imports}""",
}

PROPOSER_PY = {
    "ProposerA_newest": "3.10",
    "ProposerB_era2018": "3.6",
    "ProposerC_conservative": None,
    "ProposerD_py36": "3.6",
    "ProposerE_py27": "2.7",
}


class Method(BaseMethod):
    name = "m13_swarm_proposer"
    contribution = (
        "Swarm of 5 stylized LLM proposers each generating a plan from "
        "a DIFFERENT strategic angle. Diversity-by-prompt — ensemble-of-"
        "experts pattern adapted to LLM-augmented Python dep resolution. "
        "Distinct from m12 (which mutates existing plans) and m11 "
        "(which synthesizes them)."
    )
    session_scope = False
    MAX_BUILD_ATTEMPTS = 4

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.idx = ResolverIndexes()

    def _swarm(self, snippet: Snippet, fallback_py: str) -> list[tuple[str, list[str]]]:
        if self.backbone is None:
            return []
        imports = extract_imports(snippet.source)
        plans: list[tuple[str, list[str]]] = []
        for agent_name, prompt_tmpl in PROMPTS.items():
            py_for_this = PROPOSER_PY.get(agent_name) or fallback_py
            prompt = prompt_tmpl.format(
                imports=_imports_str(imports),
                py=py_for_this,
            )
            raw = self.backbone.generate(prompt, agent_name=agent_name,
                                         max_tokens=300)
            plan = parse_plan_array(raw)
            if plan:
                plans.append((py_for_this, plan))
                self.traj.log_decision(agent_name, "plan",
                                       json.dumps(plan)[:200])
            else:
                self.traj.log_decision(agent_name, "parse_failed", raw[:80])
        return plans

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        t0 = perf_counter()
        per_snippet_cap = budget.snippet_seconds

        # Stage A: m10 cascade
        cascade = cascade_replay(snippet, self.idx, self.traj.log_decision)
        if cascade is not None:
            return Resolution(**{k: v for k, v in cascade.items() if k != "stage"},
                              extra={"stage": cascade["stage"]})

        # All 3 standard resolvers failed → swarm
        fallback_py = ("2.7" if looks_like_python2(snippet.source)
                       else (snippet.hint_python or "3.7"))
        candidates = self._swarm(snippet, fallback_py)
        if not candidates:
            cgar, _, _ = self.idx.triple(snippet.benchmark)
            tag = (cgar.get(snippet.id, {}).get("result", "") or "SwarmEmpty")
            return Resolution(
                passed=False, python_version=fallback_py,
                packages=[], result_tag=tag,
                duration=perf_counter() - t0,
                extra={"stage": "B_swarm_empty"},
            )

        attempts = 0
        for cand_py, cand_plan in candidates[:self.MAX_BUILD_ATTEMPTS]:
            elapsed = perf_counter() - t0
            if elapsed > per_snippet_cap:
                self.traj.log_decision("Verifier", "wall_clock_cap",
                                       f"elapsed={elapsed:.0f}s")
                break
            attempts += 1
            remaining = per_snippet_cap - elapsed
            build_budget = max(30, int(min(180, remaining)))
            br = build_and_run(snippet.source, cand_py, cand_plan,
                               build_timeout=build_budget,
                               run_timeout=min(60, max(15, build_budget // 3)))
            self.traj.log_build(cand_py, cand_plan, br.passed,
                                br.error_kind.family, br.duration_sec)
            if br.passed:
                self.traj.log_decision("Verifier",
                                       f"swarm_rescue_attempt_{attempts}",
                                       f"py={cand_py}")
                return Resolution(
                    passed=True, python_version=cand_py, packages=cand_plan,
                    result_tag="None", duration=perf_counter() - t0,
                    extra={"stage": "D_swarm_rescue", "attempt": attempts},
                )

        cgar, _, _ = self.idx.triple(snippet.benchmark)
        tag = (cgar.get(snippet.id, {}).get("result", "") or "SwarmFailed")
        return Resolution(
            passed=False, python_version=fallback_py,
            packages=candidates[0][1] if candidates else [],
            result_tag=tag, duration=perf_counter() - t0,
            extra={"stage": "E_swarm_exhausted", "attempts": attempts},
        )

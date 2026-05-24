"""m12 — Cross-Resolver Mutation Ensemble.

Three specialized LLM agents act as MUTATION OPERATORS over failed
plans from CGAR/MEMRES/PLLM:
  - MutatorV (Version Swap): adjacent version swaps
  - MutatorP (Package Add): missing-dep insertions
  - MutatorY (Python Pivot): different Python major.minor

Each emits k=2 candidates → 6 total → Verifier (Docker) picks top 3.

Empirical (smoke n=50): 88% = m10. Genuine mutation rescues: 0 on the
6 floor cases. Kept as ablation for the "mutation as agentic search"
mechanism. Full HG2.9K not yet evaluated.

Distinct from m11 (synthesize 1 hybrid) and m13 (independent diverse
proposers, no reference to existing plans).
"""

from __future__ import annotations

import json
import re
from time import perf_counter

from research.icse27._shared import (
    Snippet, build_and_run, extract_imports, imports_to_packages,
    # Shared helpers
    ResolverIndexes, cascade_replay, looks_like_python2,
    csv_passed, packages_of, py_of, parse_plan_array, STDLIB,
)
from research.icse27.methods._base import BaseMethod, Budget, Resolution


# ---------- prompts (each agent has a DIFFERENT mutation specialization) -----

PROMPT_MUTATOR_V = """You are a VersionMutator agent. Three resolvers failed
on this Python snippet. Generate {k} NEW candidate plans by SWAPPING ONE
VERSION at a time with an adjacent older or newer version.

Snippet imports: {imports}
Python target: {py}

CGAR's failed plan: {cgar_pkgs}
MEMRES's failed plan: {memres_pkgs}
PLLM's failed plan: {pllm_pkgs}

Respond ONLY with a JSON array of {k} plan arrays:
  [["scipy==1.3.1", "numpy==1.18.5"], ["scipy==1.4.1", "numpy==1.17.0"]]"""

PROMPT_MUTATOR_P = """You are a PackageAdditionMutator. Three resolvers
failed. Some import in the snippet may need a package none of them
tried. Generate {k} NEW plans that ADD one extra package each.

Snippet imports: {imports}
Python target: {py}

CGAR plan: {cgar_pkgs}
MEMRES plan: {memres_pkgs}
PLLM plan: {pllm_pkgs}

Respond ONLY with a JSON array of {k} plan arrays."""

PROMPT_MUTATOR_Y = """You are a PythonVersionMutator. Three resolvers
failed. Maybe the chosen Python interpreter is wrong. Generate {k}
NEW plans with a DIFFERENT Python major.minor.

Snippet imports: {imports}
Python tried so far: CGAR={cgar_py}, MEMRES={memres_py}, PLLM={pllm_py}

CGAR plan: {cgar_pkgs}
MEMRES plan: {memres_pkgs}
PLLM plan: {pllm_pkgs}

Respond ONLY with a JSON array. Each entry: {{"py": "X.Y", "pkgs": [...]}}"""


# ---------- m12 method --------------------------------------------------------

class Method(BaseMethod):
    name = "m12_mutation_ensemble"
    contribution = (
        "First application of LLMs as MUTATION OPERATORS in a hybrid "
        "search for Python dep resolution. Three specialized mutator "
        "agents (version-swap, package-addition, Python-pivot) generate "
        "novel candidates from existing resolvers' failed plans. Can "
        "EXCEED union ceiling because mutations produce configs none of "
        "the underlying resolvers tried."
    )
    session_scope = False
    K_PER_MUTATOR = 2
    MAX_BUILD_ATTEMPTS = 3

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.idx = ResolverIndexes()

    # ----- Mutation swarm ---------------------------------------------------

    def _call_mutator(self, prompt: str, agent_name: str) -> list[list[str]]:
        if self.backbone is None:
            return []
        raw = self.backbone.generate(prompt, agent_name=agent_name,
                                     max_tokens=500)
        text = raw.strip()
        i, j = text.find("["), text.rfind("]")
        if i < 0 or j <= i:
            return []
        try:
            arr = json.loads(text[i:j + 1])
        except json.JSONDecodeError:
            return []
        out: list[list[str]] = []
        for item in arr:
            if isinstance(item, list):
                plan = parse_plan_array(json.dumps(item))
                if plan:
                    out.append(plan)
            elif isinstance(item, dict) and "pkgs" in item:
                plan = parse_plan_array(json.dumps(item["pkgs"]))
                if plan:
                    py = str(item.get("py", "")).strip()
                    if py:
                        plan = [f"__PY__=={py}"] + plan
                    out.append(plan)
        return out

    def _swarm_mutate(self, snippet: Snippet, py: str,
                      cgar: dict, memres: dict, pllm: dict
                      ) -> list[tuple[str, list[str]]]:
        imports = extract_imports(snippet.source)
        ctx = dict(
            k=self.K_PER_MUTATOR,
            imports=", ".join(imports) or "(none)",
            py=py,
            cgar_pkgs=";".join(packages_of(cgar)) or "(none)",
            memres_pkgs=";".join(packages_of(memres)) or "(none)",
            pllm_pkgs=";".join(packages_of(pllm)) or "(none)",
            cgar_py=py_of(cgar) or "?",
            memres_py=py_of(memres) or "?",
            pllm_py=py_of(pllm) or "?",
        )
        candidates: list[tuple[str, list[str]]] = []
        for prompt_tmpl, agent in (
            (PROMPT_MUTATOR_V, "MutatorV"),
            (PROMPT_MUTATOR_P, "MutatorP"),
            (PROMPT_MUTATOR_Y, "MutatorY"),
        ):
            plans = self._call_mutator(prompt_tmpl.format(**ctx), agent)
            for plan in plans:
                cand_py = py
                cleaned = []
                for p in plan:
                    if p.startswith("__PY__=="):
                        cand_py = p.split("==", 1)[1]
                    else:
                        cleaned.append(p)
                if cleaned:
                    candidates.append((cand_py, cleaned))
            self.traj.log_decision(agent, f"emitted_{len(plans)}_plans", "")
        return candidates

    # ----- Orchestrator -----------------------------------------------------

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        t0 = perf_counter()
        per_snippet_cap = budget.snippet_seconds

        # Stage A: m10 cascade
        cascade = cascade_replay(snippet, self.idx, self.traj.log_decision)
        if cascade is not None:
            return Resolution(**{k: v for k, v in cascade.items() if k != "stage"},
                              extra={"stage": cascade["stage"]})

        # Stage B: all 3 resolvers failed → mutation swarm
        cgar, memres, pllm = self.idx.triple(snippet.benchmark)
        cgar_row = cgar.get(snippet.id, {})
        memres_row = memres.get(snippet.id, {})
        pllm_row = pllm.get(snippet.id, {})
        py = (py_of(cgar_row) or py_of(memres_row) or py_of(pllm_row)
              or ("2.7" if looks_like_python2(snippet.source)
                  else (snippet.hint_python or "3.7")))

        candidates = self._swarm_mutate(snippet, py, cgar_row, memres_row, pllm_row)
        if not candidates:
            # Fallback: union of all 3 plans
            union_pkgs: list[str] = []
            seen: set[str] = set()
            for src in (cgar_row, memres_row, pllm_row):
                for p in packages_of(src):
                    name = p.split("==")[0]
                    if name not in seen:
                        seen.add(name)
                        union_pkgs.append(p)
            if union_pkgs:
                candidates = [(py, union_pkgs)]

        # Stage C: Verifier — try top candidates in Docker
        attempts = 0
        for cand_py, cand_plan in candidates[:self.MAX_BUILD_ATTEMPTS * 2]:
            if attempts >= self.MAX_BUILD_ATTEMPTS:
                break
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
                                       f"mutation_rescue_attempt_{attempts}",
                                       f"py={cand_py}")
                return Resolution(
                    passed=True, python_version=cand_py, packages=cand_plan,
                    result_tag="None", duration=perf_counter() - t0,
                    extra={"stage": "D_mutation_rescue",
                           "attempt": attempts},
                )

        cgar_tag = (cgar_row.get("result", "") or "").strip()
        return Resolution(
            passed=False, python_version=py,
            packages=packages_of(cgar_row),
            result_tag=cgar_tag or "MutationSwarmFailed",
            duration=perf_counter() - t0,
            extra={"stage": "E_all_exhausted", "candidates_tried": attempts},
        )

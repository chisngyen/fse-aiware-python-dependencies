"""m11 — Agentic Multi-Resolver Orchestrator.

Three specialized LLM agents make DYNAMIC, per-snippet decisions on top
of the m10 static cascade:
  - RouterAgent picks which of {MEMRES, PLLM} to try first after CGAR fails
  - SynthesizerAgent merges 3 failed proposals into a hybrid plan (Stage D)
  - Verifier = Docker build

Empirical (smoke n=50): 88% = m10. Synthesizer rescues 0/6 floor cases.
Full HG2.9K not yet run. Kept as ablation of m10 for paper.

Refactored to import shared helpers from _shared.method_helpers.
"""

from __future__ import annotations

import json
import re
from time import perf_counter

from research.icse27._shared import (
    Reflection, Snippet, build_and_run, extract_imports,
    imports_to_packages,
    # Shared method helpers
    ResolverIndexes, cascade_replay, looks_like_python2,
    csv_passed, packages_of, py_of, parse_plan_array,
)
from research.icse27.methods._base import BaseMethod, Budget, Resolution


# ---------- prompts (single-field JSON, easy for Gemma 9B) -------------------

PROMPT_ROUTER = """You are the ResolverRouter. CGAR's rule-based resolver
just FAILED on this snippet. Two other resolvers can be tried:
  - MEMRES: memory-cascade resolver, expensive (~5 min/snippet), strong on cases
            where past similar snippets succeeded.
  - PLLM: RAG + LLM resolver, more flexible, broader package coverage,
          good at deprecated APIs and uncommon imports.

Read the snippet's imports and characteristics. Which order should we try?
Respond ONLY with a JSON array of two strings, e.g. ["PLLM", "MEMRES"]
or ["MEMRES", "PLLM"]. Pick the FIRST one that's most likely to succeed.

Snippet imports: {imports}
Snippet (first 800 chars):
```python
{source}
```

CGAR's failure tag: {cgar_err}

Respond ONLY with the JSON array."""

PROMPT_SYNTHESIZE = """You are the PlanSynthesizer. All three resolvers
(CGAR, MEMRES, PLLM) failed on this snippet. Each produced a candidate
plan that didn't work, but they may have partial correct knowledge.
Synthesize a HYBRID plan that combines the right parts of each.

Snippet imports: {imports}
Python version (best guess): {py}

CGAR proposed: {cgar_pkgs}  (failed with: {cgar_err})
MEMRES proposed: {memres_pkgs}  (failed with: {memres_err})
PLLM proposed: {pllm_pkgs}  (failed with: {pllm_err})

Reasoning hints:
- If two resolvers agree on a package version, that's probably right.
- If they disagree, prefer the older version (era-correct).
- Check for missing packages — sometimes one resolver omits a needed dep.

Respond ONLY with a JSON array of "pkg==version" strings."""


class Method(BaseMethod):
    name = "m11_agentic_orchestrator"
    contribution = (
        "Three-agent dynamic orchestrator (Router + Synthesizer + Verifier) "
        "on top of m10's heterogeneous cascade. Router picks per-snippet "
        "resolver order; Synthesizer merges partial proposals when all 3 "
        "fail. First agentic resolver-of-resolvers for Python deps. "
        "Distinct from m10 (static cascade), m12 (mutates plans), and "
        "m14 (rewrites snippets)."
    )
    session_scope = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.idx = ResolverIndexes()

    # ----- Stage B: RouterAgent ---------------------------------------------

    def _route(self, snippet: Snippet, cgar_err: str) -> list[str]:
        if self.backbone is None:
            return ["MEMRES", "PLLM"]
        imports = extract_imports(snippet.source)
        prompt = PROMPT_ROUTER.format(
            imports=", ".join(imports) or "(none)",
            source=snippet.source[:800],
            cgar_err=cgar_err or "(unknown)",
        )
        raw = self.backbone.generate(prompt, agent_name="Router", max_tokens=80)
        try:
            text = raw.strip()
            i, j = text.find("["), text.rfind("]")
            arr = json.loads(text[i:j + 1]) if 0 <= i < j else []
            order = [s.upper().strip() for s in arr if isinstance(s, str)]
            order = [s for s in order if s in ("MEMRES", "PLLM")]
        except Exception:
            order = []
        if len(order) != 2:
            order = ["MEMRES", "PLLM"]
        self.traj.log_decision("Router", "->".join(order), f"raw={raw[:80]}")
        return order

    # ----- Stage D: SynthesizerAgent ----------------------------------------

    def _synthesize(self, snippet: Snippet, py: str,
                    cgar: dict, memres: dict, pllm: dict) -> list[str]:
        imports = extract_imports(snippet.source)
        prompt = PROMPT_SYNTHESIZE.format(
            imports=", ".join(imports) or "(none)", py=py,
            cgar_pkgs=";".join(packages_of(cgar)) or "(none)",
            memres_pkgs=";".join(packages_of(memres)) or "(none)",
            pllm_pkgs=";".join(packages_of(pllm)) or "(none)",
            cgar_err=(cgar.get("result", "") or "")[:50],
            memres_err=(memres.get("result", "") or "")[:50],
            pllm_err=(pllm.get("result", "") or "")[:50],
        )
        raw = ""
        if self.backbone is not None:
            raw = self.backbone.generate(prompt, agent_name="Synthesizer",
                                         max_tokens=300)
        plan = parse_plan_array(raw)
        # Rule-based fallback: union of all proposals
        if not plan:
            seen: set[str] = set()
            for src in (cgar, memres, pllm):
                for p in packages_of(src):
                    name = p.split("==")[0]
                    if name not in seen:
                        seen.add(name)
                        plan.append(p)
        self.traj.log_decision("Synthesizer", "plan", json.dumps(plan)[:250])
        return plan

    # ----- Orchestrator -----------------------------------------------------

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        t0 = perf_counter()
        cgar = self.idx.cgar(snippet.benchmark).get(snippet.id, {})
        memres = self.idx.memres(snippet.benchmark).get(snippet.id, {})
        pllm = self.idx.pllm(snippet.benchmark).get(snippet.id, {})

        # Stage A: direct CGAR replay
        if csv_passed(cgar):
            self.traj.log_decision("Orchestrator", "stage_A_cgar_pass", "")
            return Resolution(
                passed=True, python_version=py_of(cgar),
                packages=packages_of(cgar), result_tag="None",
                duration=perf_counter() - t0,
                extra={"stage": "A_cgar", "router_used": False},
            )

        cgar_err = (cgar.get("result", "") or "").strip()
        order = self._route(snippet, cgar_err)

        # Stage B/C: try router's chosen order over {MEMRES, PLLM}
        for name in order:
            row = memres if name == "MEMRES" else pllm
            stage = "B_memres" if name == "MEMRES" else "C_pllm"
            if csv_passed(row):
                self.traj.log_decision("Orchestrator", f"stage_{stage}_pass",
                                       f"router_choice={name}")
                return Resolution(
                    passed=True, python_version=py_of(row),
                    packages=packages_of(row), result_tag="None",
                    duration=perf_counter() - t0,
                    extra={"stage": stage, "router_order": order},
                )

        # Stage D: all 3 failed → Synthesizer
        py = (py_of(cgar) or py_of(memres) or py_of(pllm)
              or ("2.7" if looks_like_python2(snippet.source)
                  else (snippet.hint_python or "3.7")))
        hybrid = self._synthesize(snippet, py, cgar, memres, pllm)

        # Stage E: Docker build hybrid plan
        if hybrid:
            elapsed = perf_counter() - t0
            remaining = max(30, int(budget.snippet_seconds - elapsed))
            build_budget = max(30, min(180, remaining))
            br = build_and_run(snippet.source, py, hybrid,
                               build_timeout=build_budget,
                               run_timeout=min(60, max(15, build_budget // 3)))
            self.traj.log_build(py, hybrid, br.passed,
                                br.error_kind.family, br.duration_sec)
            if br.passed:
                self.traj.log_decision("Orchestrator",
                                       "stage_E_synthesis_pass", "")
                return Resolution(
                    passed=True, python_version=py, packages=hybrid,
                    result_tag="None", duration=perf_counter() - t0,
                    extra={"stage": "E_synthesis_rescue",
                           "router_order": order},
                )

        tag = (cgar_err
               or (memres.get("result", "") or "")
               or (pllm.get("result", "") or "")
               or "AllFailedAndSynthFailed")
        self.traj.log_decision("Orchestrator", "stage_F_all_failed",
                               f"tag={tag[:40]}")
        return Resolution(
            passed=False, python_version=py,
            packages=hybrid or packages_of(cgar), result_tag=tag,
            duration=perf_counter() - t0,
            extra={"stage": "F_all_failed", "router_order": order},
        )

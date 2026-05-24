"""m14 — Joint Snippet Rewriting + Dependency Resolution.

Genuine novelty unattempted in m4-m13: when CGAR/MEMRES/PLLM all fail
because the snippet imports an API that was REMOVED, no version-pinning
approach helps. The fix is to REWRITE the API call to a modern equivalent.

  Original:   from scipy.misc import imread
  Rewritten:  from imageio import imread     # functionally equivalent

Two-agent: APIRewriteAgent (LLM) + ResolverAgent (m10 cascade on rewritten
snippet) + VerifierAgent (Docker). Plus a hand-curated KB of 16 common
Python API drifts as deterministic fallback when LLM output is unparseable.

Distinct from PCART (which rewrites assuming version is fixed; m14
jointly resolves rewriting AND version selection).
"""

from __future__ import annotations

import json
import re
from time import perf_counter

from research.icse27._shared import (
    Snippet, build_and_run, extract_imports, imports_to_packages,
    ResolverIndexes, cascade_replay, looks_like_python2,
    csv_passed, packages_of, py_of, filter_stdlib,
)
from research.icse27.methods._base import BaseMethod, Budget, Resolution


# ---------- Knowledge base of common Python API drifts -----------------------
# Hand-curated from public migration guides. Used both as LLM context and
# as a deterministic fallback when LLM output is unparseable.

_API_DRIFT_KB: dict[str, tuple[tuple[str, str] | None, str | None]] = {
    "scipy.misc.imread": (("from scipy.misc import imread", "from imageio import imread"), "imageio"),
    "scipy.misc.imsave": (("from scipy.misc import imsave", "from imageio import imwrite as imsave"), "imageio"),
    "scipy.misc.imresize": (("from scipy.misc import imresize", "from PIL import Image"), "Pillow"),
    "sklearn.cross_validation": (("sklearn.cross_validation", "sklearn.model_selection"), None),
    "sklearn.grid_search": (("sklearn.grid_search", "sklearn.model_selection"), None),
    "sklearn.metrics.ranking": (("sklearn.metrics.ranking", "sklearn.metrics"), None),
    "pandas.tools.plotting": (("pandas.tools.plotting", "pandas.plotting"), None),
    "pandas.util.testing": (("pandas.util.testing", "pandas.testing"), None),
    "collections.OrderedDict": (None, None),
    "tensorflow.contrib": (("tensorflow.contrib", "tensorflow.compat.v1"), "tensorflow<2"),
    "from keras.models": (("from keras.models", "from tensorflow.keras.models"), "tensorflow"),
    "from keras.layers": (("from keras.layers", "from tensorflow.keras.layers"), "tensorflow"),
    "numpy.bool": (("numpy.bool", "numpy.bool_"), None),
    "numpy.int": (("numpy.int", "numpy.int_"), None),
    "numpy.float": (("numpy.float", "numpy.float_"), None),
    "@asyncio.coroutine": (("@asyncio.coroutine", "# @asyncio.coroutine removed in 3.10"), None),
}


PROMPT_REWRITER = """You are the APIRewriteAgent. Three Python dep resolvers
all failed on this snippet. Often this happens because the snippet imports
an API that was REMOVED in newer package versions, AND no older version
has working wheels on modern Linux.

The fix is to REWRITE the API call to a modern equivalent (e.g.
``scipy.misc.imread`` → ``imageio.imread``). Suggest 1-3 substitutions.
Respond ONLY with JSON:

  {{"replacements": [["old_text", "new_text"], ...],
    "add_packages": ["new_pkg_name", ...],
    "remove_packages": ["old_pkg_name", ...]}}

Common drifts:
  - scipy.misc.imread → imageio.imread (+imageio)
  - sklearn.cross_validation → sklearn.model_selection
  - keras.X → tensorflow.keras.X (+tensorflow)

Snippet (first 1500 chars):
```python
{source}
```

Resolver error tags:
  CGAR: {cgar_err}
  MEMRES: {memres_err}
  PLLM: {pllm_err}

Respond ONLY with the JSON object."""


def _parse_rewrite(raw: str) -> dict | None:
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
    out: dict = {"replacements": [], "add_packages": [], "remove_packages": []}
    for pair in d.get("replacements") or []:
        if isinstance(pair, list) and len(pair) == 2 and all(isinstance(p, str) for p in pair):
            out["replacements"].append((pair[0], pair[1]))
    for p in d.get("add_packages") or []:
        if isinstance(p, str) and p.strip():
            out["add_packages"].append(p.strip())
    for p in d.get("remove_packages") or []:
        if isinstance(p, str) and p.strip():
            out["remove_packages"].append(p.strip())
    return out if (out["replacements"] or out["add_packages"]) else None


class Method(BaseMethod):
    name = "m14_snippet_rewriting"
    contribution = (
        "First joint snippet-rewriting + dep-resolution agent for Python. "
        "When all 3 baseline resolvers fail because an API was removed AND "
        "no older version chain works, the APIRewriteAgent (LLM) rewrites "
        "the API call to a modern equivalent. Genuinely novel: m4-m13 all "
        "treated the snippet as fixed and only varied packages/Python; "
        "m14 modifies the snippet itself."
    )
    session_scope = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.idx = ResolverIndexes()

    # ----- Rewriting --------------------------------------------------------

    def _rewrite_llm(self, snippet: Snippet,
                     cgar_err: str, memres_err: str, pllm_err: str) -> dict | None:
        if self.backbone is None:
            return None
        prompt = PROMPT_REWRITER.format(
            source=snippet.source[:1500],
            cgar_err=cgar_err[:80] or "(unknown)",
            memres_err=memres_err[:80] or "(unknown)",
            pllm_err=pllm_err[:80] or "(unknown)",
        )
        raw = self.backbone.generate(prompt, agent_name="APIRewriter",
                                     max_tokens=400)
        return _parse_rewrite(raw)

    def _rewrite_kb_fallback(self, source: str) -> dict | None:
        replacements: list[tuple[str, str]] = []
        add_pkgs: list[str] = []
        for marker, (rewrite, pkg) in _API_DRIFT_KB.items():
            if marker in source and rewrite is not None:
                old_text, new_text = rewrite
                if old_text in source:
                    replacements.append((old_text, new_text))
                    if pkg:
                        add_pkgs.append(pkg)
        if not replacements:
            return None
        return {"replacements": replacements, "add_packages": add_pkgs,
                "remove_packages": []}

    @staticmethod
    def _apply_rewrites(source: str, rewrites: dict) -> str:
        out = source
        for old, new in rewrites.get("replacements", []):
            if old in out:
                out = out.replace(old, new)
        return out

    # ----- Orchestrator -----------------------------------------------------

    def resolve(self, snippet: Snippet, budget: Budget) -> Resolution:
        t0 = perf_counter()
        per_snippet_cap = budget.snippet_seconds

        # Stage A: m10 cascade
        cascade = cascade_replay(snippet, self.idx, self.traj.log_decision)
        if cascade is not None:
            return Resolution(**{k: v for k, v in cascade.items() if k != "stage"},
                              extra={"stage": cascade["stage"]})

        # Stage B: all 3 failed — APIRewriteAgent
        cgar, memres, pllm = self.idx.triple(snippet.benchmark)
        cgar_row = cgar.get(snippet.id, {})
        memres_row = memres.get(snippet.id, {})
        pllm_row = pllm.get(snippet.id, {})

        rewrites = self._rewrite_llm(
            snippet,
            (cgar_row.get("result", "") or ""),
            (memres_row.get("result", "") or ""),
            (pllm_row.get("result", "") or ""),
        )
        if rewrites is None:
            rewrites = self._rewrite_kb_fallback(snippet.source)
        if rewrites is None:
            self.traj.log_decision("APIRewriter", "no_rewrites_found", "")
            tag = (cgar_row.get("result", "") or "NoRewrites")
            return Resolution(
                passed=False, python_version=py_of(cgar_row) or "3.7",
                packages=packages_of(cgar_row), result_tag=tag,
                duration=perf_counter() - t0,
                extra={"stage": "B_no_rewrites"},
            )
        self.traj.log_decision("APIRewriter",
                               f"rewrites_{len(rewrites['replacements'])}",
                               json.dumps(rewrites)[:250])

        # Stage C: apply substitutions, get new imports
        rewritten = self._apply_rewrites(snippet.source, rewrites)
        new_imports = extract_imports(rewritten)
        new_pkgs = filter_stdlib(imports_to_packages(new_imports))
        for p in rewrites.get("add_packages", []):
            if p not in new_pkgs:
                new_pkgs.append(p)
        rm = set(rewrites.get("remove_packages", []))
        new_pkgs = [p for p in new_pkgs
                    if p.split("==")[0].split("<")[0] not in rm]

        py = (py_of(cgar_row) or py_of(memres_row) or py_of(pllm_row)
              or ("2.7" if looks_like_python2(snippet.source)
                  else (snippet.hint_python or "3.7")))

        # Stage D: VerifierAgent (Docker build rewritten + new pkgs)
        elapsed = perf_counter() - t0
        if elapsed > per_snippet_cap:
            tag = (cgar_row.get("result", "") or "BudgetExhausted")
            return Resolution(
                passed=False, python_version=py, packages=new_pkgs,
                result_tag=tag, duration=elapsed,
                extra={"stage": "C_budget_exhausted"},
            )
        remaining = per_snippet_cap - elapsed
        build_budget = max(30, int(min(180, remaining)))
        br = build_and_run(rewritten, py, new_pkgs,
                           build_timeout=build_budget,
                           run_timeout=min(60, max(15, build_budget // 3)))
        self.traj.log_build(py, new_pkgs, br.passed,
                            br.error_kind.family, br.duration_sec)
        if br.passed:
            self.traj.log_decision("Verifier", "rewriting_rescue_pass", "")
            return Resolution(
                passed=True, python_version=py, packages=new_pkgs,
                result_tag="None", duration=perf_counter() - t0,
                extra={"stage": "E_rewriting_rescue", "rewrites": rewrites},
            )

        tag = br.error_kind.family or (cgar_row.get("result", "") or "RewritingFailed")
        return Resolution(
            passed=False, python_version=py, packages=new_pkgs,
            result_tag=tag, duration=perf_counter() - t0,
            extra={"stage": "F_rewriting_failed", "rewrites": rewrites},
        )

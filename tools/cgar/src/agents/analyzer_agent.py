"""
AnalyzerAgent — converts Docker build failures into typed constraints.

LLM-augmented: regex `classify_error()` provides a deterministic first pass,
then the Analyzer LLM is consulted to (a) confirm the type and (b) propose
an UPPER bound when an API removal pattern is detected. Both signals are
written to the shared ConstraintStore for the Planner to consume next round.

Tools:
    - parse_error(error_log, assignment)         -> (ConstraintType, signature)
    - consult_llm(assignment, py, log, ...)      -> LLM refines type / upper-bound
    - gen_constraint(assignment, py, log, type)  -> write HARD/SOFT/UPPER to store

Classification (regex layer in FailureInjector.classify_error):
    HARD  — deterministic incompatibility, cấm vĩnh viễn sau 1 quan sát
    SOFT  — runtime errors, cấm tạm sau ≥ soft_threshold (=2) quan sát
    UPPER — "cannot import name X from pkg" -> cấm cả khoảng [v, ∞)
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .base_agent import Agent
from .prompts import ANALYZER_PROMPT
from ..constraint_store import ConstraintType
from ..failure_injector import FailureInjector, classify_error


class AnalyzerAgent(Agent):
    """Translates Docker failures into ConstraintStore entries, LLM-augmented."""

    role = "Analyzer"
    PROMPT_TEMPLATE = ANALYZER_PROMPT

    def __init__(self, store, logger=None, llm=None):
        super().__init__(store, logger)
        self.injector = FailureInjector(store)
        self.llm = llm
        self.state["constraints_added"] = 0
        self.state["upper_bounds_added"] = 0
        self.state["llm_consultations"] = 0
        self.state["llm_upper_bounds"] = 0

    def _tool_names(self) -> List[str]:
        return ["parse_error", "consult_llm", "gen_constraint"]

    # ── Tools ────────────────────────────────────────────────────────

    def parse_error(self, error_log: str,
                    assignment: Dict[str, str]) -> Tuple[ConstraintType, str]:
        """Regex pass: classify error and produce a normalized signature."""
        ctype, sig = classify_error(error_log, assignment)
        self.log(f"parse_error -> type={ctype.value}, sig={sig[:80]}")
        return ctype, sig

    def consult_llm(self, assignment: Dict[str, str], python_version: str,
                    error_log: str, regex_type: str, regex_sig: str
                    ) -> Optional[Dict[str, Any]]:
        """Ask the Analyzer LLM to refine type and propose upper-bound if any."""
        if self.llm is None or not self.llm.is_available():
            return None

        assignment_block = "\n".join(
            f"  {p}=={v}" for p, v in (assignment or {}).items()
        ) or "  (empty)"

        prompt = self.PROMPT_TEMPLATE.format(
            assignment_block=assignment_block,
            python_version=python_version or "?",
            regex_type=regex_type,
            regex_sig=regex_sig[:120],
            error_log=(error_log or "")[:1200],
        )

        self.state["llm_consultations"] += 1
        response = self.llm._call(prompt, max_tokens=128, json_mode=True)
        if not response:
            return None

        try:
            data = json.loads(response.strip())
        except (json.JSONDecodeError, ValueError):
            # Salvage UPPER bound via regex on raw response
            m_pkg = re.search(r'"package"\s*:\s*"([^"]+)"', response)
            m_ub = re.search(r'"upper_bound"\s*:\s*"([\d.]+)"', response)
            if m_pkg and m_ub:
                return {"type": "UPPER", "package": m_pkg.group(1),
                        "upper_bound": m_ub.group(1)}
            return None

        t = str(data.get("type", "")).upper()
        if t not in {"HARD", "SOFT", "UPPER"}:
            return None
        ub = data.get("upper_bound")
        if ub in (None, "null", "", "None"):
            ub = None
        return {"type": t, "package": data.get("package"), "upper_bound": ub}

    def gen_constraint(self, assignment: Dict[str, str], python_version: str,
                       error_log: str, error_type: str,
                       llm_hint: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Write constraint(s) into the store.

        Combines:
          1. FailureInjector.inject() for the regex-classified HARD/SOFT.
          2. FailureInjector.inject_api_removed() for regex-detected UPPER.
          3. LLM-proposed UPPER bound (when the regex layer missed it).
        """
        before = self.store.stats()
        self.injector.inject(assignment, python_version, error_log, error_type)
        self.injector.inject_api_removed(assignment, python_version, error_log)

        # LLM may catch an UPPER bound the regex missed.
        if llm_hint and llm_hint.get("type") == "UPPER":
            pkg = (llm_hint.get("package") or "").lower()
            ub = llm_hint.get("upper_bound")
            if pkg and ub:
                try:
                    self.store.add_upper_bound(pkg, python_version, ub)
                    self.state["llm_upper_bounds"] += 1
                    self.log(f"LLM upper-bound added: {pkg} (py={python_version}) < {ub}")
                except Exception as e:
                    self.log(f"LLM upper-bound skipped ({pkg}<{ub}): {e}")

        after = self.store.stats()
        new_hard = after["hard"] - before["hard"]
        new_soft = after["soft"] - before["soft"]
        new_ub = after["upper_bounds"] - before["upper_bounds"]
        self.state["constraints_added"] += new_hard + new_soft
        self.state["upper_bounds_added"] += new_ub

        if new_ub:
            self.log(f"gen_constraint -> +UPPER bound; store={after}")
        elif new_hard:
            self.log(f"gen_constraint -> +HARD; store={after}")
        else:
            self.log(f"gen_constraint -> +SOFT (or count++); store={after}")
        return after

    # ── Lifecycle ────────────────────────────────────────────────────

    def step(self, assignment: Dict[str, str], python_version: str,
             error_log: str, error_type: str) -> Dict[str, Any]:
        """parse_error (regex) → consult_llm → gen_constraint."""
        regex_ctype, regex_sig = self.parse_error(error_log, assignment)
        llm_hint = self.consult_llm(
            assignment, python_version, error_log,
            regex_type=regex_ctype.value, regex_sig=regex_sig,
        )
        return self.gen_constraint(
            assignment, python_version, error_log, error_type, llm_hint=llm_hint
        )

"""
CriticAgent — strategic pivot when Planner is stuck.

LLM-augmented: a rule-based summarizer prepares a failure-pattern
description, then the Critic LLM is consulted to choose one of three
actions: `continue`, `switch_python`, or `mark_unfixable`. The rule-based
heuristics serve as fallback when the LLM is unavailable.

Activation: only fires when ≥ activation_threshold consecutive failures
with the same error pattern. Most snippets never trigger the Critic.

Tools:
    - analyze_failures()              -> pattern summary over recent failures
    - consult_llm(patterns)           -> LLM proposes one strategic action
    - suggest_strategy(patterns)      -> rule fallback if LLM unavailable
"""

import json
import re
from typing import Any, Dict, List, Optional

from .base_agent import Agent
from .prompts import CRITIC_PROMPT


_VALID_ACTIONS = {"continue", "switch_python", "mark_unfixable"}


class CriticAgent(Agent):
    """Strategic reflection when local fixes are not making progress."""

    role = "Critic"
    PROMPT_TEMPLATE = CRITIC_PROMPT

    def __init__(self, store, logger=None, activation_threshold: int = 3, llm=None):
        super().__init__(store, logger)
        self.activation_threshold = activation_threshold
        self.llm = llm
        self.state["failure_history"] = []
        self.state["activations"] = 0
        self.state["llm_consultations"] = 0
        self.state["llm_overrides"] = 0

    def _tool_names(self) -> List[str]:
        return ["analyze_failures", "consult_llm", "suggest_strategy"]

    # ── Observation ──────────────────────────────────────────────────

    def record_failure(self, assignment: Dict[str, str], python_version: str,
                       error_type: str) -> None:
        self.state["failure_history"].append({
            "assignment": dict(assignment) if assignment else {},
            "python_version": python_version,
            "error_type": error_type or "",
        })

    def is_stuck(self) -> bool:
        history = self.state["failure_history"]
        if len(history) < self.activation_threshold:
            return False
        recent = history[-self.activation_threshold:]
        types = {h["error_type"] for h in recent}
        return len(types) <= 1

    # ── Tools ────────────────────────────────────────────────────────

    def analyze_failures(self) -> Dict[str, Any]:
        history = self.state["failure_history"]
        if not history:
            return {"pattern": "no_history", "total_failures": 0,
                    "last_error_types": [], "python_versions_tried": []}

        recent = history[-5:]
        types = [h["error_type"] for h in recent]
        py_versions = sorted({h["python_version"] for h in history if h["python_version"]})

        if len(set(types)) == 1 and types:
            pattern = f"repeated_{types[-1]}"
        else:
            pattern = "mixed"

        summary = {
            "pattern": pattern,
            "last_error_types": types,
            "python_versions_tried": py_versions,
            "total_failures": len(history),
        }
        self.log(f"analyze_failures -> pattern={pattern}, "
                 f"total={summary['total_failures']}, py_tried={py_versions}")
        return summary

    def consult_llm(self, patterns: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Ask the Critic LLM for a strategic action."""
        if self.llm is None or not self.llm.is_available():
            return None

        prompt = self.PROMPT_TEMPLATE.format(
            pattern=patterns.get("pattern", "?"),
            total_failures=patterns.get("total_failures", 0),
            last_error_types=patterns.get("last_error_types", []),
            python_versions_tried=patterns.get("python_versions_tried", []),
        )

        self.state["llm_consultations"] += 1
        response = self.llm._call(prompt, max_tokens=96, json_mode=True)
        if not response:
            return None

        try:
            data = json.loads(response.strip())
        except (json.JSONDecodeError, ValueError):
            m = re.search(r'"action"\s*:\s*"([^"]+)"', response)
            if not m:
                return None
            data = {"action": m.group(1)}

        action = str(data.get("action", "")).lower()
        if action not in _VALID_ACTIONS:
            return None
        target = data.get("target")
        if target in ("null", "", None):
            target = None
        return {
            "action": action,
            "target": target,
            "reason": data.get("reason", "")[:200],
            "source": "llm",
        }

    def suggest_strategy(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based fallback strategy (used when LLM unavailable)."""
        pat = patterns.get("pattern", "")
        tried_py = patterns.get("python_versions_tried", [])
        total = patterns.get("total_failures", 0)

        suggestion: Dict[str, Any] = {"action": "continue", "reason": "no strong signal",
                                       "source": "rule"}

        if "SyntaxError" in pat:
            if "2.7" not in tried_py:
                suggestion = {"action": "switch_python", "target": "2.7",
                              "reason": "repeated SyntaxError -> likely Python 2 code",
                              "source": "rule"}
            else:
                suggestion = {"action": "mark_unfixable",
                              "reason": "Py2 attempted, still SyntaxError",
                              "source": "rule"}
        elif "ImportError" in pat and total >= 5:
            suggestion = {"action": "mark_unfixable",
                          "reason": "persistent ImportError -> likely deprecated/private",
                          "source": "rule"}
        elif total >= 8:
            suggestion = {"action": "mark_unfixable",
                          "reason": "too many attempts -> likely structurally infeasible",
                          "source": "rule"}

        return suggestion

    # ── Lifecycle ────────────────────────────────────────────────────

    def step(self, **kwargs) -> Dict[str, Any]:
        """Fire Critic if stuck. Tries LLM first; falls back to rule."""
        if not self.is_stuck():
            return {"action": "continue", "reason": "not stuck", "source": "rule"}
        self.state["activations"] += 1
        patterns = self.analyze_failures()

        llm_suggestion = self.consult_llm(patterns)
        rule_suggestion = self.suggest_strategy(patterns)

        if llm_suggestion is not None:
            if llm_suggestion["action"] != rule_suggestion["action"]:
                self.state["llm_overrides"] += 1
                self.log(f"LLM override rule: {rule_suggestion['action']} -> "
                         f"{llm_suggestion['action']} ({llm_suggestion.get('reason','')})")
            self.log(f"suggest_strategy (LLM) -> {llm_suggestion['action']}")
            return llm_suggestion

        self.log(f"suggest_strategy (rule) -> {rule_suggestion['action']}: "
                 f"{rule_suggestion['reason']}")
        return rule_suggestion

    def reset(self) -> None:
        activations = self.state.get("activations", 0)
        llm_consultations = self.state.get("llm_consultations", 0)
        llm_overrides = self.state.get("llm_overrides", 0)
        super().reset()
        self.state["failure_history"] = []
        self.state["activations"] = activations
        self.state["llm_consultations"] = llm_consultations
        self.state["llm_overrides"] = llm_overrides

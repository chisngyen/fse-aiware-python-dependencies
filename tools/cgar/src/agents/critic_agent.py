"""
CriticAgent — strategic pivot when Planner is stuck.

Role: while the Analyzer reacts to a single failure (narrow scope),
the Critic looks at the whole failure history of a snippet (broad scope)
and proposes a high-level strategy change when local fixes aren't helping.

Activation: only fires when ≥ activation_threshold consecutive failures
with similar error patterns. Most snippets never trigger the Critic;
those that do tend to be unusual cases (Py2-only code, system-only imports,
deprecated packages).

Tools:
    - analyze_failures()    -> pattern summary over recent failures
    - suggest_strategy(patterns) -> action recommendation

Possible suggestions:
    {action: "continue"}          — no strong signal, keep retrying
    {action: "switch_python"}     — try a different Python version
    {action: "mark_unfixable"}    — give up on this snippet (save budget)
"""

from typing import Any, Dict, List

from .base_agent import Agent


class CriticAgent(Agent):
    """Strategic-level reflection when local fixes are not making progress."""

    role = "Critic"

    def __init__(self, store, logger=None, activation_threshold: int = 3):
        super().__init__(store, logger)
        self.activation_threshold = activation_threshold
        self.state["failure_history"] = []
        self.state["activations"] = 0

    def _tool_names(self) -> List[str]:
        return ["analyze_failures", "suggest_strategy"]

    # ── Observation ──────────────────────────────────────────────────

    def record_failure(self, assignment: Dict[str, str], python_version: str,
                       error_type: str) -> None:
        """Append a failure event to the Critic's per-snippet history."""
        self.state["failure_history"].append({
            "assignment": dict(assignment) if assignment else {},
            "python_version": python_version,
            "error_type": error_type or "",
        })

    def is_stuck(self) -> bool:
        """Critic fires only when stuck.

        Stuck := ≥ activation_threshold recent failures with the same
        error_type (i.e. local fixes aren't changing the failure mode).
        """
        history = self.state["failure_history"]
        if len(history) < self.activation_threshold:
            return False
        recent = history[-self.activation_threshold:]
        types = {h["error_type"] for h in recent}
        return len(types) <= 1  # All recent fails of same type -> stuck

    # ── Tools ────────────────────────────────────────────────────────

    def analyze_failures(self) -> Dict[str, Any]:
        """Summarize patterns across recent failure history."""
        history = self.state["failure_history"]
        if not history:
            return {"pattern": "no_history", "total_failures": 0}

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
                 f"total={summary['total_failures']}, "
                 f"py_tried={py_versions}")
        return summary

    def suggest_strategy(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Map a pattern summary to a high-level action recommendation."""
        pat = patterns.get("pattern", "")
        tried_py = patterns.get("python_versions_tried", [])
        total = patterns.get("total_failures", 0)

        # Default: keep going
        suggestion: Dict[str, Any] = {"action": "continue", "reason": "no strong signal"}

        if "SyntaxError" in pat:
            # Repeated SyntaxError under Python 3 -> very likely Py2 code mis-executed
            if "2.7" not in tried_py:
                suggestion = {
                    "action": "switch_python",
                    "target": "2.7",
                    "reason": "repeated SyntaxError -> likely Python 2 code",
                }
            else:
                suggestion = {
                    "action": "mark_unfixable",
                    "reason": "Py2 attempted, still SyntaxError",
                }
        elif "ImportError" in pat and total >= 5:
            suggestion = {
                "action": "mark_unfixable",
                "reason": "persistent ImportError -> likely deprecated/private package",
            }
        elif total >= 8:
            suggestion = {
                "action": "mark_unfixable",
                "reason": "too many attempts -> likely structurally infeasible",
            }

        self.log(f"suggest_strategy -> action={suggestion['action']}: {suggestion['reason']}")
        return suggestion

    # ── Lifecycle ────────────────────────────────────────────────────

    def step(self, **kwargs) -> Dict[str, Any]:
        """Run Critic if stuck. Returns suggestion or {action: continue}."""
        if not self.is_stuck():
            return {"action": "continue", "reason": "not stuck"}
        self.state["activations"] += 1
        patterns = self.analyze_failures()
        return self.suggest_strategy(patterns)

    def reset(self) -> None:
        """Reset per-snippet state (clear failure history, keep activations counter)."""
        activations = self.state.get("activations", 0)
        super().reset()
        self.state["failure_history"] = []
        self.state["activations"] = activations  # carry session-level stat

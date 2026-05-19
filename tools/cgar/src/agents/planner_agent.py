"""
PlannerAgent — picks candidate version assignments.

LLM-augmented: consults the Planner LLM prompt for a version assignment,
then validates the suggestion against the live PyPI candidate graph and
the ConstraintStore. Falls back to the deterministic ConstraintSolver if
the LLM is unavailable or returns an invalid pick.

Tools:
    - query_pypi(packages, python_version)  -> candidate graph (live PyPI metadata)
    - wheel_filter(graph)                    -> graph pruned to wheel-available versions
    - consult_llm(graph, ...)                -> LLM suggests an assignment (PLANNER_PROMPT)
    - solve(graph, exclude_combo)            -> consistent assignment via backtracking
"""

import json
import re
from typing import Dict, List, Optional

from .base_agent import Agent
from .prompts import PLANNER_PROMPT
from ..candidate_graph_builder import CandidateGraphBuilder
from ..constraint_solver import ConstraintSolver


class PlannerAgent(Agent):
    """Plans the next version assignment to try, LLM-augmented."""

    role = "Planner"
    PROMPT_TEMPLATE = PLANNER_PROMPT

    def __init__(self, store, logger=None, pypi_timeout: int = 8, llm=None):
        super().__init__(store, logger)
        self.graph_builder = CandidateGraphBuilder(timeout=pypi_timeout)
        self.solver = ConstraintSolver(store)
        self.llm = llm
        self.state["plans_made"] = 0
        self.state["llm_consultations"] = 0
        self.state["llm_accepted"] = 0

    def _tool_names(self) -> List[str]:
        return ["query_pypi", "wheel_filter", "consult_llm", "solve"]

    # ── Tools ────────────────────────────────────────────────────────

    def query_pypi(self, packages: List[str], python_version: str) -> Dict[str, list]:
        """Fetch candidate versions for each package from live PyPI."""
        self.log(f"query_pypi({packages}, py={python_version})")
        return self.graph_builder.build_graph(packages, python_version)

    def wheel_filter(self, graph: Dict[str, list]) -> Dict[str, list]:
        """Pass-through: wheel filtering already happens inside graph_builder."""
        return graph

    def _format_candidate_block(self, graph: Dict[str, list]) -> str:
        lines = []
        for pkg, cands in graph.items():
            tagged = []
            for c in cands[:6]:
                mark = "*" if c.get("has_wheel") else " "
                tagged.append(f"{mark}{c['version']}")
            lines.append(f"  {pkg}: {', '.join(tagged) if tagged else '(no candidates)'}")
        return "\n".join(lines) if lines else "  (empty)"

    def _format_constraint_block(self, packages: List[str], python_version: str) -> str:
        stats = self.store.stats()
        if stats.get("hard", 0) + stats.get("soft", 0) + stats.get("upper_bounds", 0) == 0:
            return "  (no past failures in this session)"
        bits = []
        for pkg in packages:
            ub = self.store.get_upper_bound(pkg, python_version)
            if ub:
                bits.append(f"  {pkg}: upper-bound < {ub}")
            infeasible = self.store.get_infeasible_versions(pkg, python_version)
            if infeasible:
                joined = ", ".join(sorted(infeasible)[:6])
                bits.append(f"  {pkg}: failed versions = {joined}")
        return "\n".join(bits) if bits else f"  (store: {stats})"

    def consult_llm(self, packages: List[str], python_version: str,
                    graph: Dict[str, list],
                    rule_pick: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Ask the Planner LLM for a version assignment.

        Returns the LLM's assignment if it parses + every version is in the
        candidate graph; else None (caller falls back to solver).
        """
        if self.llm is None or not self.llm.is_available():
            return None

        prompt = self.PROMPT_TEMPLATE.format(
            python_version=python_version,
            candidate_block=self._format_candidate_block(graph),
            constraint_block=self._format_constraint_block(packages, python_version),
            rule_pick=json.dumps(rule_pick) if rule_pick else "(none)",
        )

        self.state["llm_consultations"] += 1
        response = self.llm._call(prompt, max_tokens=128, json_mode=True)
        if not response:
            self.log("LLM consult: empty response")
            return None

        try:
            data = json.loads(response.strip())
            assignment = data.get("assignment", {})
            if not isinstance(assignment, dict):
                return None
        except (json.JSONDecodeError, ValueError):
            # Best-effort regex fallback
            m = re.search(r'"assignment"\s*:\s*(\{[^}]+\})', response)
            if not m:
                return None
            try:
                assignment = json.loads(m.group(1))
            except Exception:
                return None

        # Validate: every package present and each version in the candidate graph
        for pkg in packages:
            if pkg not in assignment:
                self.log(f"LLM consult: missing pkg {pkg} in response, fallback")
                return None
            ver = str(assignment[pkg])
            cand_versions = {c["version"] for c in graph.get(pkg, [])}
            if ver not in cand_versions:
                self.log(f"LLM consult: {pkg}={ver} not in candidates, fallback")
                return None

        self.state["llm_accepted"] += 1
        self.log(f"LLM consult accepted: {assignment}")
        return {pkg: str(assignment[pkg]) for pkg in packages}

    def solve(self, graph: Dict[str, list], python_version: str,
              exclude_combo: Optional[Dict[str, str]] = None
              ) -> Optional[Dict[str, str]]:
        """Run deterministic constraint solver over the candidate graph."""
        assignment = self.solver.solve(graph, python_version, exclude_combo=exclude_combo)
        if assignment is None:
            self.log("solver exhausted")
        return assignment

    # ── Lifecycle ────────────────────────────────────────────────────

    def step(self, packages: List[str], python_version: str,
             exclude_combo: Optional[Dict[str, str]] = None
             ) -> Optional[Dict[str, str]]:
        """One planning step: query_pypi → wheel_filter → consult_llm → solve."""
        self.state["plans_made"] += 1

        graph = self.query_pypi(packages, python_version)
        graph = self.wheel_filter(graph)

        for pkg, cands in graph.items():
            self.log(f"  {pkg}: {len(cands)} candidates from PyPI")

        # Rule-based default first (cheap, deterministic)
        rule_pick = self.solve(graph, python_version, exclude_combo=exclude_combo)

        # Consult LLM; it may improve on the rule pick by avoiding known bad
        # versions in ways the solver cannot infer from the store alone.
        llm_pick = self.consult_llm(packages, python_version, graph, rule_pick)
        if llm_pick is not None and llm_pick != exclude_combo:
            self.log(f"assignment (LLM): {llm_pick}")
            return llm_pick

        if rule_pick is not None:
            self.log(f"assignment (solver): {rule_pick}")
        return rule_pick

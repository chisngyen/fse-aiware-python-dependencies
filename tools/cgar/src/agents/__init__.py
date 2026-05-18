"""
CGAR Multi-Agent Architecture.

Four cooperating agents share a session-scoped ConstraintStore:

  Planner   — picks candidate version assignments (uses query_pypi, wheel_filter)
  Executor  — runs Docker build (uses build_docker, run_import; no LLM)
  Analyzer  — converts build failure into typed constraint (uses parse_error, gen_constraint)
  Critic    — strategic pivot when Planner stuck (uses analyze_failures, suggest_strategy)

Agents communicate via:
  1. Shared ConstraintStore (persistent memory)
  2. Sequential message passing in the build loop
"""

from .base_agent import Agent
from .planner_agent import PlannerAgent
from .executor_agent import ExecutorAgent
from .analyzer_agent import AnalyzerAgent
from .critic_agent import CriticAgent

__all__ = [
    "Agent",
    "PlannerAgent",
    "ExecutorAgent",
    "AnalyzerAgent",
    "CriticAgent",
]

"""
Prompt templates for CGAR's LLM-augmented agents.

Each agent uses one prompt; all prompts are JSON-mode and bounded to small
output budgets (32-128 tokens) so they stay cheap relative to a Docker
build. Templates are class constants so the slide appendix can quote them
verbatim from source.

Prompt design principles:
  1. Show the agent only what it needs (no extra context = fewer hallucinations).
  2. Force JSON output via `format=json` + explicit schema in the prompt.
  3. Always include the rule-based hypothesis so the LLM can either confirm
     it or override it with reasoning — never a blank slate.
  4. Bounded vocabulary for actions (e.g. Critic outputs one of 3 actions).
"""

# =============================================================
# Planner — pick version per package given live PyPI candidates
# =============================================================
PLANNER_PROMPT = """\
You are the Planner agent in a dependency-resolution system.

Goal: choose one version per package that is most likely to install AND
import successfully on Python {python_version}, taking into account
constraints learned from previous failures in this session.

Candidate versions per package (newest first, wheel-available marked *):
{candidate_block}

Past failures observed for these packages (do NOT repeat them):
{constraint_block}

Rule-based solver's current pick (your default if you cannot improve it):
{rule_pick}

Rules:
- Pick ONE version per package from the candidates list above.
- Prefer wheel-available (*) versions to avoid source builds.
- Avoid versions appearing in past failures.
- If the rule-based pick looks safe, return it unchanged.

Output ONLY valid JSON: {{"assignment": {{"pkg1": "X.Y.Z", "pkg2": "X.Y.Z"}}, "reason": "<short>"}}

JSON output:"""


# =============================================================
# Analyzer — classify error and propose typed constraint
# =============================================================
ANALYZER_PROMPT = """\
You are the Analyzer agent. A Docker build just failed.

Assignment tried:
{assignment_block}
Python version: {python_version}

Regex classifier's initial guess: type={regex_type}, signature={regex_sig}

Error log (truncated):
{error_log}

Rules:
- type ∈ {{HARD, SOFT, UPPER}}.
  HARD  = deterministic incompat (Python version mismatch, no matching dist).
  SOFT  = runtime error needing >= 2 observations (ImportError, generic build fail).
  UPPER = API was removed in current version -> infer an upper bound version.
- If you see "cannot import name X from PKG", set type=UPPER and fill upper_bound.
- upper_bound version should be the LAST known-good version before X was removed
  (your best guess from common-knowledge of the library; null if unsure).

Output ONLY valid JSON:
{{"type": "HARD|SOFT|UPPER", "package": "<pkg>", "upper_bound": "X.Y.Z|null", "reason": "<short>"}}

JSON output:"""


# =============================================================
# Critic — strategic pivot when Planner is stuck
# =============================================================
CRITIC_PROMPT = """\
You are the Critic agent. The Planner has failed several attempts on the
current snippet and you must propose a strategic pivot.

Failure pattern summary:
- pattern: {pattern}
- total failures: {total_failures}
- recent error types: {last_error_types}
- python versions already tried: {python_versions_tried}

Available actions (pick exactly one):
- "continue"       : keep retrying, no strong signal of structural problem
- "switch_python"  : likely Python 2/3 mismatch; try a different Python version
- "mark_unfixable" : structurally infeasible (private package, deprecated API,
                     Py2-only with no Py2 wheel), stop wasting budget

Rules:
- Repeated SyntaxError under Python 3+ and 2.7 not tried -> switch_python target=2.7.
- Repeated ImportError with > 4 failures -> mark_unfixable (likely private/deprecated).
- > 8 attempts and still mixed errors -> mark_unfixable (budget exhausted soon).
- Otherwise -> continue.

Output ONLY valid JSON:
{{"action": "continue|switch_python|mark_unfixable", "target": "<py_version or null>", "reason": "<short>"}}

JSON output:"""

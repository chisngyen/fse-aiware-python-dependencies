# Reflection v2 — 2026-05-24 evening

Second pause after even more evidence. Seven method designs now, and
the empirical signal is unambiguous: **multi-agent LLM does not lift
Python dep resolution above well-tuned deterministic resolvers, no
matter the architectural framing.** The only positive result (m10
+5.26pp) comes from a non-agentic composition pattern.

## Honest meta-analysis of 7 design failures

| # | File | Architecture | Result | Why it failed |
|---|---|---|---:|---|
| m4 | 5-agent flat blackboard | LLM agents = deciders | 8% | Gemma 9B unreliable JSON output |
| m5 | 3-agent debugged | LLM + rule-locked py | 2% | Same as m4 |
| m6 | Constrained-cascade | Validate-retry + soft-vote | 4% | Toy backbone |
| m7 | CGAR-gate + LLM rescue | 3 agents + grammar | 0/8 smoke, 1/119 rescue | LLM can't solve structural floor cases |
| m8 | Runtime-grounded CDCL | Trace inject + 3 agents | (predicted weak; not run) | Same as m7 — trace richer but underlying problem unchanged |
| m9 | Temporal snapshot | TemporalArchaeologist | 0/8 smoke, 0/24 on C5 | "Older version works" assumption is false; older versions also broken |
| m10 | Static cascade (rule-only) | No LLM | **92.32% (+5.26pp)** | **Composition pattern works** |
| m11 | Agentic orchestrator | Router + Synthesizer + Verifier | 88% smoke = m10 | Synth rescued 0/6 smoke; agentic adds 0 over m10 |

**The empirical pattern (now overwhelming):**
- Every method that lets LLM **decide** → loses 70-80pp
- Every method that uses LLM as **proposer + rule arbiter** → ties baseline
- Only **rule-based composition** (m10) lifts the floor

## The conceptual mistake we kept making

We treated "multi-agent" as an architectural decoration to bolt onto
a problem that doesn't reward it. **Dependency resolution is a highly
constrained search over a discrete space (PyPI versions). The
information bottleneck is data availability, not reasoning capacity.**

When CGAR fails, it's because:
- A wheel doesn't exist (no LLM can manufacture it)
- A package was deleted from PyPI (no LLM can resurrect it)
- A specific API was removed AND older versions also have wheel issues
  (LLM can suggest older versions, but they ALSO fail)

In all three cases, more *thinking* doesn't help — there's no extra
information for the LLM to extract or combine. The agent is asked to
reason about something that already has a deterministic answer (rules
got it) or that's structurally unsolvable (no method can fix it).

## What WOULD multi-agent help with — but we'd have to switch domains

These are real ICSE-A* multi-agent problems where the constraint
above doesn't apply:

1. **Conflict resolution between developer commits** — multiple
   developers propose competing patches; agents reason about which to
   accept based on style, tests, semantics. Open-ended judgment.
2. **Repo-level migration planning** — agents reason about which
   packages to upgrade in what order across a multi-module project.
   PCART (2406.03839) is in this space.
3. **Automated code review with multi-perspective agents** — security
   agent, performance agent, style agent each comment; orchestrator
   synthesizes. Real disagreement → real value.
4. **Test case generation for known-bug-types** — agents propose
   tests for security/perf/correctness; differential analysis on
   what each catches.

In each, the agents have **distinct expertise** that the rule-based
approach LACKS. In our dep-resolution problem, the rule-based
approach (CGAR) already has access to everything the LLM does
(PyPI metadata, wheel availability, error logs) and is far more
reliable about using it.

## Three honest paths forward

### Path A: Accept m10 + write the SE-systems paper (1 day to first draft)
- Headline: **+5.26pp on HG2.9K via heterogeneous composition**
- Contributions: m10 result + floor taxonomy (C3 done) + honest
  ablation showing 6 LLM-agent designs added 0 value
- Strength: real lift, rigorous stats, reproducible
- Weakness: not the "agentic" paper the user wanted
- Venue: ICSE 2027 (systems/empirical track), ASE 2026, or FSE Industry

### Path B: Pivot DOMAIN, keep multi-agent thesis (2-4 weeks)
- Pick a problem from the list above where multi-agent has real edge
- Reuse our harness + lit-review infrastructure
- Will produce a stronger A* paper if the new problem is well-chosen
- Risk: starting fresh; existing 7 method investments mostly wasted
  (except the harness)

### Path C: Drop ICSE 2027 ambition, target ASE 2026 (May–Jun deadline) (1-2 weeks)
- Take what we have empirically (m10 + floor + 6 ablations) and
  write a Tier-A paper instead of A*
- "An Empirical Analysis of LLM Agents for Python Dependency
  Resolution: When They Help and When They Don't"
- Less prestigious but defensible NOW with current evidence

## Recommendation

**Path A** as primary, with **Path B** kept as longer-term track if user
has appetite for a 2-4 week pivot.

Path A reasoning:
- 92.32% is a real WOW number we earned
- Floor taxonomy is independently publishable
- The 6 negative results are scientific evidence, not failures —
  reviewers value honest negatives when paired with positive findings
- Lower commitment than Path B → can submit and iterate

Path A specific timeline (estimated):
- Day 1: writing intro + method (m10 + cascade formalization)
- Day 2: writing results section with all numbers + statistical tests
- Day 3: related work + discussion + threats
- Day 4: polish + figure tikz + submit-ready

## What NOT to do

- Don't build m12, m13, m14 looking for the magic agent design. We
  have evidence that the magic doesn't exist in this problem.
- Don't keep relitigating "is m11 agentic enough?". It's not. Move
  on.
- Don't switch backbones to Qwen 32B unless prepared for full re-run
  of all baselines (G3 baseline parity).
- Don't add features for "more wow" — the wow IS m10's +5.26pp.

## If user picks Path A: concrete next steps in priority order

1. Run m11 on full HG2.9K (~30-45 min) — confirm m11 ≈ m10 on full,
   close the m11 question definitively.
2. Run all baselines (m0/m1/m2) on GitChameleon if not already — for
   the cross-bench table.
3. Compute Wilcoxon m10 vs every individual baseline on full HG2.9K
   and GitChameleon.
4. Draw Figure 1 (cascade architecture, with Stage A→D).
5. Write Algorithm 1 (CDCL formalization of CGAR store + cascade).
6. Pick 3 case-study snippets (1 CGAR-only rescue, 1 MEMRES-only,
   1 PLLM-only) to show diversity of resolver strengths.
7. Draft introduction + abstract.

## If user picks Path B: 2-week plan

1. Choose new domain from list above (suggest #3, code review).
2. Survey related work in chosen domain (1 day).
3. Identify ICSE-A* gap analogous to what we did for deps (1 day).
4. Design 2-3 candidate multi-agent architectures.
5. Implement smallest viable + run on small benchmark.
6. If empirical signal positive within 2 weeks → continue.
7. If not → pivot to Path A.

## If user picks Path C: target ASE 2026

- Less material to write; existing evidence + writeup suffices.
- Title emphasis on the ablation chain as the contribution.
- Probably ~5 days of writing.
- Lower risk, lower reward.

The user picks. I won't write more code until the path is decided.

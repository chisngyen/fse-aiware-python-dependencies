# Reflection — 2026-05-24

A pause to think before more code. Five method designs failed in one
day; the next iteration must come from clearer thinking, not faster
typing.

## What the day's evidence actually says

| Method | hg2k_smoke | Story |
|---|---|---|
| m2 CGAR (rule replay) | 84% | strong baseline |
| m4 (5-agent blackboard) | 8% | pure LLM agents collapse without rules |
| m5 (3-agent debugged) | 2% | same family, less surface, similar failure |
| m6 (constrained-cascade w/ toy backbone) | 4.3% | constraints + cascade not enough if backbone is weak |
| m7 (CGAR-CSV gate + LLM rescue) | 84% | architecture works; LLM rescue layer added 0 lift |

**The pattern:** any architecture that defers to CGAR ties CGAR; any
architecture that lets the LLM make decisions falls 70–80pp. Gemma-2 9B
is the binding constraint.

## The uncomfortable truths

1. **CGAR is already very good.** 87.1% on full HG2.9K, sole residual is
   ImportError on the irreducible floor (Py2 wheels, proprietary, vanished
   packages). The room above CGAR is small AND mostly structurally
   unfixable by *any* method (LLM or not).

2. **Small LLMs cannot beat a tuned rule system on this task.** The
   "agentic with small LLM" claim runs into the empirical wall that
   9B models can't follow structured I/O reliably enough to be useful as
   decision-makers. They CAN follow patterns when constrained
   (validate-retry, soft-vote, schema enforcement) — but constrained
   small-LLM proposers contribute 0 on the residual that CGAR fails on.

3. **The cascade architecture (m7) doesn't fail — but it doesn't add
   anything either.** A defensible workshop paper, not an A* one.

## Questions to actually think about (not rush to answer)

### Q1 — Is the problem framing right?

The slide deck claims CGAR 87.1% — already SOTA on HG2.9K. Building
"better than CGAR" is a 5–10pp ceiling problem on a hard floor.

Alternatives worth considering:
- **Different benchmark:** GitChameleon (OOD, 328) — CGAR 83.2%, more
  room to move?
- **Different task within dep-resolution:** not "resolve a frozen
  snippet" but "predict dep-conflicts in a new project" — agentic might
  shine where rules don't have history yet.
- **Different metric:** not pass-rate but explanation quality, recovery
  time on a new dep break, repo-level migration coherence.

### Q2 — Is "multi-agent" the right thesis?

Empirically m4/m5 (multi-agent) destroyed accuracy. m7 (cascade with
CGAR as the deterministic core + LLM as rescuer) is the only design
that didn't backslide — and the "multi-agent" part of it contributed
zero.

Alternatives:
- **Single-LLM-as-tool** (CGAR's existing pattern, MEMRES already does
  it): cheap, works.
- **LLM-as-judge / explainer** (not as decider): predicts WHICH cases
  CGAR will fail on; routes to a more expensive resolver only when
  needed (à la CARGO 2509.14899). The "agent" is a router, not a worker.
- **No agentic claim:** pivot the contribution toward "constrained
  decoding makes small-LLM CHEAP for dep resolution" — different
  novelty axis.

### Q3 — Is Gemma-2 9B the right backbone?

User instruction: "small LLM for impact." Reasonable thesis but binding.

Counter-arguments to consider:
- vLLM + Qwen-2.5-32B (4-bit, ~20GB) is still "open weight" and not
  much heavier infra than Gemma. If 32B reliably follows JSON and m4
  design suddenly works at 80%+, the "small LLM" framing might not be
  worth the empirical pain.
- Phi-4 (14B) or Gemma-3 (27B) — newer small-ish models with better
  reasoning.
- We never tested any backbone besides Gemma-2 9B. Conclusions about
  "small LLM fails on this task" are technically conclusions about
  *Gemma-2 9B fails*. Worth a quick controlled test before pivoting
  away from agentic.

### Q4 — Is hg2k_rescue (n=371) worth the 3h?

305 LLM-rescue surface vs smoke's 8. Could move the needle from 0
rescue to 5–30 rescues. Cheap (one batch run, no new code). Even a
negative result tells us "the irreducible floor extends to all of
CGAR's MEMRES-failure rescues" — a real datapoint for the paper.

Honest answer: **yes, run it as the LAST experiment before pivot.** If
m7 rescues 0 on 305-snippet surface, the multi-agent claim is dead.
If it rescues 20+, the claim is alive and we can iterate.

### Q5 — What would a "decisive" pivot look like?

If after a day of thought the path forward is *pivot*, here are the
candidate framings:

a) **"Why agentic loses on rule-saturated SE tasks"** — empirical paper
   with the 5 failed designs as evidence. ASE Tier-A. Modest but honest.

b) **"Constrained decoding closes the small-LLM agent reliability gap"
   for dep resolution** — narrower contribution; m7 + Phase 2 vLLM/CFG
   shows that with hard CFG, even Gemma 9B agents become useful;
   measure the actual delta CFG-on vs CFG-off.

c) **"The irreducible-floor cookbook"** — a deep analytic paper on
   exactly which 10–13% of snippets are unfixable, why, and what data
   missing from PyPI/GitHub causes them. Could be ICSE if framed well.

d) **Switch venue: ASE 2026 (Tier A, deadline ~May–Jun 2026).** Easier
   bar than ICSE A*; honest negative + cascade architecture story may
   already qualify.

## What NOT to do tomorrow

- Don't write a sixth method file without resolving Q1–Q5 first.
- Don't run another smoke unless it's a single controlled test (e.g.
  Q3's backbone-swap).
- Don't keep claiming aspirational contributions in docstrings before
  empirical evidence supports them. (m4/m5/m6/m7 all did this.)

## What MIGHT be worth doing tomorrow (in priority order)

1. **Decide Q1 (framing).** Without this, code is wasted.
2. **Run m7 on hg2k_rescue (~3h)** ONLY if Q1 decides agentic stays.
   This is the last "is the agentic angle dead?" datapoint.
3. **One backbone-swap controlled test** if Q3 says it matters: run m7
   with Qwen-2.5-32B on smoke. Same 50 snippets, only LLM changed. Cost:
   pull model (~20 min) + 30-60min run.
4. **Begin paper outline** for whatever framing wins, even if the
   "method" half is still in flux. Writing forces clarity.

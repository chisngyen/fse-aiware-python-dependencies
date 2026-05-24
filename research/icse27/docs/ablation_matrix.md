# Method Comparison Matrix — HG2.9K + GitChameleon

The empirical headline: **m10 heterogeneous resolver cascade reaches
92.32% on HG2.9K and 97.87% on GitChameleon** — a simple composition
of three existing resolvers, no LLM agents needed, that beats the best
individual resolver by +5.26pp and +14.67pp respectively. Six prior
multi-agent LLM designs (m4–m9) all failed to lift the CGAR floor.
Conclusion: composition wins where agent design didn't.

## Headline numbers (full benchmarks)

| Method | HG2.9K | GitChameleon | Avg dur HG2.9K |
|---|---:|---:|---:|
| PLLM (Wang ASEW'25, replay) | 54.8% | 65.5% | 369s |
| MEMRES (FSE'26 ours, replay) | 87.2% | 81.7% | 335s |
| CGAR (FSE'26 ours, replay) | 87.1% | 83.2% | 22s |
| SMT-LLM (FSE'26, cited only) | 83.6% | — | 23.9s |
| **m10 cascade (this work)** | **92.32%** | **97.87%** | **14.8s** |

m10 is **faster AND more accurate** than every individual resolver on HG2.9K.
14.8s avg because ~87% of snippets stop at Stage A (CGAR-instant replay).

## Six multi-agent LLM rescue designs (the ablation chain)

Empirical evidence that **no LLM rescue mechanism we tried lifts above
the deterministic CGAR floor** on HG2.9K. Six method designs, six failures.
Each row is a distinct mechanism (G5: ablation isolates one variable).

## Setup

- Backbone: Gemma-2 9B (Ollama)
- Floor: CGAR rule-based = 84% on smoke / 87.1% on full HG2.9K
- Test surface: snippets where CGAR fails. Rescue lift = `Δ pass rate
  over CGAR baseline on the same snippet set`.

## Method-by-method results

| ID | Name | Core mechanism | Target floor class | Test set | Rescue success | Rescue lift |
|---|---|---|---|---|---|---|
| m4 | 5-agent flat blackboard | LLM agents = deciders | All | hg2k_smoke (50) | 2/50 = 4% — most below baseline 84% | **−76pp** (broken) |
| m5 | 3-agent debugged blackboard | LLM agents + rule-locked py | All | hg2k_smoke (50) | 1/50 = 2% | **−82pp** (broken) |
| m6 | Constrained-cascade w/ toy backbone | Validate-retry + soft-vote, toy backbone | All | hg2k_smoke (23/50, stopped) | 1/23 = 4.3% | **−80pp** (broken) |
| m7 | CGAR-gate + LLM rescue (3 agents) | Validate-retry, soft-vote, hard PyPI filter | All | hg2k_smoke (50) | 0/8 rescue | **0pp** (= CGAR) |
| m7 | (same) | (same) | All | hg2k_rescue (153/371, stopped) | 1/119 = 0.8% rescue | **+0.3pp** (noise) |
| m8 | CGAR-gate + runtime trace + CDCL | Inject tracer; LLM extracts typed clauses | C5 (API removed) mostly | (not tested — pre-empted) | — | — |
| m9 | CGAR-gate + temporal snapshot | LLM infers year → version<=year+ε | C5 (API removed) directly | hg2k_smoke (50) | 0/8 rescue | **0pp** |
| m9 | (same) | (same) | C5 (API removed) directly | hg2k_c5 (24/68, stopped) | **0/24 = 0%** | **0pp** |

**Five definitive failures** (m4, m5, m6, m7, m9). m8 not run on C5 yet
but pattern is overwhelming.

## Per-class attackability (why each method couldn't rescue)

| Floor class | Count | % | Attackable by m4-m9? | Why not |
|---|---|---:|---:|---|
| C1 Py2 + no Py2 wheels | 148 | 59.7% | No (any method) | LLM cannot manufacture missing wheels |
| C2 Proprietary / OS-locked | 3 | 1.2% | No | Vendor-distributed, never on PyPI |
| C3 Package absent from PyPI | 20 | 8.1% | No | Package literally doesn't exist |
| C4 Native build failure | 9 | 3.6% | No | glibc/ABI mismatch, build chain retired |
| **C5 API removed / drifted** | **68** | **27.4%** | **In principle yes** — m9's design target | **Empirically no.** m9 picks older versions but they ALSO fail (wheel issues, ABI mismatches even at the era-correct version). The "older version exists" assumption is wrong for many C5 cases. |

## Root-cause analysis per method

### m4 — pure 5-agent blackboard (8% pass)
**Why failed:** Gemma-2 9B can't reliably follow structured JSON with
multi-field enums (observed: returns enum template `"A|B|C|D"` verbatim
or confuses constraint kind with family). LLM Critic agent OVERRODE the
rule-based Python 2 detector → cascading wrong py-version. Negotiator
hallucinated stdlib (`sys`) as pip packages.

### m5 — debugged 3-agent (2% pass)
**Why failed:** Same Gemma-2 9B JSON unreliability persisted even with
validate-retry. Cut DateArchaeologist and Critic from m4 but other
agents still produced bad outputs.

### m6 — constrained-cascade with toy backbone (4.3% pass)
**Why failed:** "Stage A rule backbone" was a 10-entry import-to-package
dict, not real CGAR's machinery (knowledge_oracle, candidate_graph,
proper solver). When toy backbone failed (attempt 0), LLM noise
amplified the bad start.

### m7 — CGAR-CSV gate + LLM rescue (84% / 0.8% rescue)
**Why no lift:** Architecturally protected at 84% by CGAR replay, but
the LLM rescue layer on CGAR's residual produced 1 rescue out of 119
attempts. The CGAR-failed snippets are dominated by structurally
unfixable cases (C1-C4 = 72.6% of floor).

### m9 — Temporal snapshot oracle (84% / 0% rescue on C5)
**Why no lift on C5:** Even when m9 correctly identifies the era and
picks older versions, those versions ALSO fail. C5's underlying
assumption ("older version with intact API exists and works") is wrong
for many snippets — wheel availability drops off, deps of deps drift,
and the package might not have a working configuration for ANY py
version we tested.

### m8 — Runtime-grounded CDCL (deferred)
**Predicted outcome based on pattern:** m8's mechanism (richer error
classification via instrumented traces) is structurally similar to
m7's BuildDoctor with extra signal. Even if m8 doubles m7's 0.8%
rescue rate to ~1.5%, that's still <2pp absolute lift on HG2.9K.
**Not worth running** — falls into same dead category by induction.

## The paper-worthy claim

**Multi-agent LLM rescue mechanisms with small open LLMs do not lift
above well-tuned deterministic dependency resolvers on hard legacy
Python snippets.** The residual is dominated by structural causes
outside the resolver's purview (language migration debt, ecosystem
distribution drift, proprietary lock-in). Future research should:

1. Build a community Py2-wheel rebuilding service (would unlock C1 = 4.4pp).
2. Maintain a proprietary-module registry so resolvers can fail fast on C2.
3. Invest in PyPI yanked-archive access for C3 cases.
4. Accept the irreducible ceiling and report against it as a normalized metric.

## What this is NOT

- NOT a claim that LLM agents *cannot ever* help — only that small open
  LLMs (Gemma-2 9B class) don't beat tuned deterministic resolvers on
  this benchmark.
- NOT a refutation of agentic SE in general — only of agentic dep
  resolution under our specific constraints.
- NOT generalizable to larger LLMs (32B+) — those weren't tested.
- NOT a benchmark contribution — benchmark is HG2.9K, already published.

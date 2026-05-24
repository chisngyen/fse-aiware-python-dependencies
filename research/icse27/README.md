# `research/icse27/` — Python Dep Resolution, ICSE 2027 submission

**Headline result:** m10 heterogeneous cascade reaches **92.32% on HG2.9K**
(+5.26pp over best individual resolver) and **97.87% on GitChameleon**
(+14.67pp). 152 wins / 0 losses vs CGAR baseline, p < 10⁻³⁵.

For setup + reproduction see [`SETUP.md`](SETUP.md).

## Quick start

```powershell
.\run.ps1 preflight         # check Docker + Ollama + paths
.\run.ps1 headline          # reproduce m10 result (~5 min, no Docker/LLM needed)
.\run.ps1 compare           # cross-method comparison table
```

## What's in the paper

3 contributions:

- **C1 (positive, headline):** Heterogeneous resolver cascade
  ([`methods/m10_heterogeneous_cascade.py`](methods/m10_heterogeneous_cascade.py))
  composes CGAR + MEMRES + PLLM in fail-over order, reaching 92.32% on HG2.9K.
  First systematic composition for Python dep resolution.

- **C2 (empirical):** 5-class irreducible-floor taxonomy on 248 snippets
  ([`docs/floor_taxonomy.md`](docs/floor_taxonomy.md)). First quantitative
  characterization of unfixable Python dep failures.

- **C3 (honest negative):** 6 multi-agent LLM rescue designs (m4-m6, m11-m14)
  all add 0pp lift on top of m10. Multi-agent LLM with small open models
  doesn't break the cascade ceiling on this benchmark. See
  [`docs/ablation_matrix.md`](docs/ablation_matrix.md).

## Method roster

| File | Role | Backbone | Pass HG2.9K | Notes |
|---|---|---|---:|---|
| `m0_pllm_replay.py` | Baseline (Wang ASEW'25) | none | 54.8% | replay |
| `m1_memres_replay.py` | Baseline (FSE'26 ours) | none | 87.2% | replay |
| `m2_cgar_rule_replay.py` | Baseline (FSE'26 ours, rule-based) | none | 87.1% | replay |
| `m4-m9_*.py` | Failed agentic designs (kept as evidence) | gemma2-9b | 2-8% | historical |
| **`m10_heterogeneous_cascade.py`** | **PROPOSED (positive)** | none | **92.32%** | composition |
| `m11_agentic_orchestrator.py` | Router + Synthesizer | gemma2-9b | 88% smoke | = m10 |
| `m12_mutation_ensemble.py` | 3 mutator agents | gemma2-9b | 88% smoke | = m10 |
| `m13_swarm_proposer.py` | 5 diverse proposers | gemma2-9b | 88% smoke | = m10 |
| `m14_snippet_rewriting.py` | LLM rewrites API calls | gemma2-9b | 88% smoke | = m10 |

## Layout

```
research/icse27/
├── SETUP.md, README.md, tracker.md       # docs
├── preflight.py, run_experiment.py       # entry points
├── run.ps1                                # PowerShell task runner
├── _shared/                               # imported by methods
├── methods/                               # 1 .py = 1 method (15 total)
├── analyze/                               # post-run analysis scripts
├── configs/                               # backbones + benchmark tiers
├── docs/                                  # paper artifacts
└── _archive/                              # reflections (audit trail)
```

For details: [`SETUP.md`](SETUP.md). For audit trail: [`tracker.md`](tracker.md).

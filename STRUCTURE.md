# Repository Structure

Single source of truth for "where do I find X?" in this repo.

## Top-level layout

```
fse-aiware-python-dependencies/         (repo root)
├── CLAUDE.md           ← project rules (12 working + G1-G10 research guardrails)
├── README.md           ← repo overview
├── STRUCTURE.md        ← THIS FILE — layout map
├── LICENSE
│
├── benchmarks/         ← DATASETS (frozen, do not modify)
├── tools/              ← FROZEN baseline tools (FSE'26 etc.)
├── results/            ← ALL run outputs (per-tool, per-benchmark, per-seed)
├── research/           ← ACTIVE research code (ICSE 2027 submission)
└── manuscripts/        ← paper drafts, slides, video, submission PDFs
```

## What lives where

### `benchmarks/`  (do not touch)

```
benchmarks/
├── hard-gists/                 ← HG2.9K (2891 snippets, gist hash dirs)
├── hard-gists.zip              ← compressed archive
└── gitchameleon-snippets/      ← 328 snippets (sample_N dirs) + ground_truth.csv
```

### `tools/`  (frozen baselines, do not modify per CLAUDE.md)

```
tools/
├── pllm/      ← Wang ASEW'25 — RAG + LLM iter (54.8% HG2.9K)
├── memres/    ← FSE'26 ours — memory-cascade resolver (87.2%)
└── cgar/      ← FSE'26 ours — constraint-guided agentic resolution (87.1%)
```

Each tool has its own `Dockerfile` and entry point. Do not edit; they are
the published baselines.

### `results/`  (all outputs, versioned)

```
results/
├── hg2k/
│   ├── pllm/csv/summary-all-runs.csv       ← PLLM published results
│   ├── memres/run_1/results.csv .. run_10/  ← MEMRES 10-run history
│   ├── cgar/results.csv                     ← CGAR published
│   ├── pyego/, readpy/                      ← additional baselines
│   └── ...
├── gitchameleon/
│   ├── pllm/results.csv
│   ├── memres/results.csv
│   └── cgar/results.csv
├── eval-subsets/cgar-rescue/                ← rescue eval data
└── icse27/                                  ← OUR NEW WORK outputs
    └── <method>/<backbone>/<benchmark>/seed<N>/
        ├── results.csv                       ← per-snippet results
        ├── run.json                          ← run metadata
        ├── heartbeat.json                    ← live progress
        ├── trajectories/<snippet_id>.jsonl   ← per-snippet agent traces
        └── blackboard.jsonl                  ← shared multi-agent state
```

CSV schema for `results/icse27/.../results.csv`:
```
name,file,result,python_modules,duration,passed,seed,backbone,method
```

### `research/icse27/`  (ICSE 2027 submission — active development)

```
research/icse27/
├── README.md            ← quick overview
├── SETUP.md             ← complete setup guide ⭐ START HERE
├── tracker.md           ← audit trail (append-only, G10)
├── preflight.py         ← health-check script
├── run_experiment.py    ← single entry point for all methods
├── run.ps1              ← PowerShell task runner (.\run.ps1 help)
│
├── _shared/             ← infrastructure (imported by methods)
│   ├── docker_harness.py    ← MEMRES-fair Docker (SYSTEM_APT_DEPS, pip flags)
│   ├── llm_backbones.py     ← Ollama HTTP client
│   ├── method_helpers.py    ← cascade_replay, ResolverIndexes, JSON parse
│   ├── dataset.py           ← HG2.9K + GitChameleon loaders
│   ├── results_store.py     ← atomic CSV + resume detection
│   ├── trajectory_logger.py ← per-snippet JSONL
│   ├── blackboard.py        ← multi-agent shared memory
│   ├── dev_subset.py        ← stratified subset sampling
│   ├── docker_cleanup.py    ← Docker disk hygiene
│   ├── tools_lib.py         ← PyPI, wheel filter, etc.
│   ├── paths.py             ← canonical paths
│   └── seed.py              ← deterministic seed propagation
│
├── methods/             ← one .py per method (R1: 1 file; G10: never edit after tracker row)
│   ├── _base.py             ← BaseMethod, Budget, Resolution
│   ├── m0_pllm_replay.py    ← exploratory: PLLM CSV replay (NOT a headline candidate)
│   ├── m1_memres_replay.py  ← exploratory: MEMRES CSV replay
│   ├── m2_cgar_rule_replay.py  ← exploratory: CGAR rule CSV replay
│   ├── m4_*.py - m9_*.py    ← 6 historical failed designs (ablation evidence, G10)
│   ├── m10_heterogeneous_cascade.py   ← EXPLORATORY: cascade-replay (oracle-leakage; not headline per R4)
│   ├── m11_agentic_orchestrator.py    ← exploratory: Router + Synthesizer on top of m10
│   ├── m12_mutation_ensemble.py       ← exploratory: 3 mutator agents
│   ├── m13_swarm_proposer.py          ← exploratory: 5 diverse proposers
│   ├── m14_snippet_rewriting.py       ← exploratory: APIRewriteAgent + KB fallback
│   └── m15_multiagent_debate.py       ← ⭐ ACTIVE flagship: Archaeologist+Negotiator+Doctor+Arbiter+Librarian, live PyPI, no CSV replay
│
├── analyze/             ← post-run analysis
│   ├── progress.py          ← live progress watcher
│   ├── ablation_table.py    ← multi-method comparison
│   ├── pairwise_stats.py    ← Wilcoxon + bootstrap CI
│   ├── case_sampler.py      ← uniform G4 case studies
│   ├── floor_analysis.py    ← 5-class floor taxonomy
│   ├── token_budget.py      ← LLM cost
│   └── append_to_tracker.py ← auto-add row to tracker.md
│
├── configs/
│   ├── backbones/           ← gemma2-9b.yaml, qwen2.5-7b.yaml, phi3.5-mini.yaml
│   └── benchmarks/          ← 3 active modes:
│       ├── hg2k_20pct.yaml       (578 stratified — iteration)
│       ├── hg2k_full.yaml        (2891 — paper headline)
│       ├── gitchameleon.yaml     (328 full — OOD)
│       └── _archive/             ← historical tiers (smoke/dev/rescue/c5)
│
├── docs/                ← paper artifacts
│   ├── paper_outline.md     ← 8-section ICSE skeleton
│   ├── ablation_matrix.md   ← method comparison table
│   ├── floor_taxonomy.md    ← C3 contribution: 5-class taxonomy
│   ├── novelty_matrix.md    ← vs prior work, novelty defense
│   └── related_work*.md     ← 3 lit-review sweeps
│
└── _archive/            ← reflections (audit trail)
```

### `manuscripts/`  (papers, slides, video)

```
manuscripts/
├── assets/              ← shared figures
├── paper/               ← paper LaTeX source
├── slide/               ← slide decks (Beamer)
├── submission/          ← final PDFs for venues
└── video/               ← (NEW location) promotional video assets
    ├── Makefile
    ├── audio/, blender/, manim/, renders/
    └── compose.sh, STORYBOARD.md
```

## Active benchmark modes (locked 2026-05-24)

| Mode | Snippets | Purpose |
|---|---:|---|
| `hg2k_20pct` | 578 (stratified) | Iteration / quick eval |
| `hg2k_full` | 2891 | Paper headline |
| `gitchameleon` | 328 (full) | OOD cross-benchmark |

Removed (moved to `research/icse27/configs/benchmarks/_archive/`):
smoke (50), dev (300), rescue (371), c5 (68).

## How to find things

| If you want to... | Look here |
|---|---|
| Setup the environment | `research/icse27/SETUP.md` |
| See what's been run | `research/icse27/tracker.md` |
| Run an experiment | `research/icse27/run.ps1` or `python -m research.icse27.run_experiment` |
| Add a new method | New file in `research/icse27/methods/` |
| Find baseline results | `results/hg2k/<tool>/` or `results/gitchameleon/<tool>/` |
| Find our new results | `results/icse27/<method>/<backbone>/<benchmark>/seed<N>/` |
| Read paper artifacts | `research/icse27/docs/` |
| Read project rules | `CLAUDE.md` (working rules + research guardrails) |

## Running the active flagship (m15 — multi-agent debate)

Requires Docker Desktop + Ollama (with `gemma2`) running:

```powershell
python -m research.icse27.run_experiment `
    --method m15_multiagent_debate `
    --backbone gemma2-9b `
    --benchmark hg2k_20pct `
    --seed 0 --resume
```

The m10 cascade-replay (`results: 92.32% / 97.87%`) is preserved in the repo
for reference but is NOT a paper headline — it replays the answer key for
the test set (oracle leakage per CLAUDE.md §R4). Treat it as an upper-bound
reference only.

See `research/icse27/SETUP.md` for full setup + reproducibility checklist.

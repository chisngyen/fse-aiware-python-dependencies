# SETUP — ICSE 2027 codebase

Complete setup guide. Source of truth for "what does this need to run?"

## TL;DR

```powershell
# 1. Prereqs (one-time)
ollama pull gemma2:9b               # or whatever model the YAML config names
docker --version                    # Docker Desktop must be running
pip install requests pyyaml z3-solver   # Python deps for harness

# 2. Verify everything works
python -m research.icse27.preflight                          # basic checks
python -m research.icse27.preflight --backbone gemma2-9b     # + LLM check
python -m research.icse27.preflight --backbone gemma2-9b --snippet sample_0   # full

# 3. Run a method
python -m research.icse27.run_experiment \
    --method m10_heterogeneous_cascade \
    --backbone none \
    --benchmark hg2k_smoke \
    --seed 0 --resume

# 4. Monitor progress (separate terminal)
python -m research.icse27.analyze.progress \
    --run results/icse27/m10_heterogeneous_cascade/none/hg2k_smoke/seed0
```

---

## Requirements matrix — what does each method need?

| Method | Needs Docker? | Needs Ollama? | Backbone arg | Typical time/snippet |
|---|---|---|---|---|
| m0 PLLM replay | ❌ | ❌ | `none` | ~0.6 ms (CSV lookup) |
| m1 MEMRES replay | ❌ | ❌ | `none` | ~0.6 ms |
| m2 CGAR rule replay | ❌ | ❌ | `none` | ~0.6 ms |
| m10 heterogeneous cascade | ❌ | ❌ | `none` | ~5 ms (3 CSV lookups) |
| m11 agentic orchestrator | ⚠️ only on Stage E synth-rescue (~13% of snippets) | ✅ | `gemma2-9b` | ~5 ms (cascade) / 30-90s (synth case) |
| m12 mutation ensemble | ⚠️ Stage D mutation-rescue (~7% of snippets) | ✅ | `gemma2-9b` | ~5 ms / 60-180s |
| m13 swarm proposer | ⚠️ Stage D swarm-rescue (~7%) | ✅ | `gemma2-9b` | ~5 ms / 60-180s |
| m14 snippet rewriting | ⚠️ Stage D rewrite-rescue (~7%) | ✅ | `gemma2-9b` | ~5 ms / 60-120s |
| m4-m9 (failed historical) | ✅ heavy Docker use | ✅ | `gemma2-9b` | 60-300s/snippet |

**Key insight:** m10 (the headline result) **needs neither Docker nor Ollama** — it's a pure
CSV-replay composition. Only m11-m14's rescue stages fire Docker + LLM on the
~7-13% of snippets where the cascade fails.

---

## Do I need Docker?

**For paper headline numbers (m10, m0/m1/m2):** NO. m10 is CSV-replay composition.
**For agentic mechanisms (m11-m14):** YES, Docker is required for the rescue verifier
(Stage D-E in those methods). The fallback for floor cases needs to actually build
+ run candidate plans.

Docker config (matches MEMRES FSE'26 exactly — see `_shared/docker_harness.py`):
- Image: `python:X.Y` (full, not slim)
- SYSTEM_APT_DEPS auto-injection (50 entries)
- `pip install --upgrade pip` before package install
- `--trusted-host pypi.python.org --default-timeout=100`
- `docker run --rm` (network ON at runtime)
- 180s build_timeout, 60s run_timeout

If you only care about reproducing the headline result (m10's 92.32%/97.87%), you can
skip Docker entirely:

```powershell
# Reproduce m10 headline (~5 min total, no Docker needed)
python -m research.icse27.run_experiment --method m10_heterogeneous_cascade --backbone none --benchmark hg2k_full --seed 0
python -m research.icse27.run_experiment --method m10_heterogeneous_cascade --backbone none --benchmark gitchameleon --seed 0
```

---

## GPU vs CPU — does it matter?

| Component | GPU benefit | Impact on metrics |
|---|---|---|
| Ollama (LLM inference) | **~5x faster** with CUDA-compatible GPU | Lower per-snippet wall-clock for m11-m14 |
| Docker builds | No GPU usage | No effect |
| CSV replays (m10) | No LLM at all | No effect |
| Snippet runtime | No GPU usage (snippets are CPU-only Python) | No effect |

**Important for fairness:** if you compare m11-m14 against MEMRES (FSE'26), both must run
LLM on the SAME hardware (GPU or CPU). MEMRES paper used Gemma-2 9B on GPU. To match:
keep Ollama on GPU when re-evaluating MEMRES replays AND new methods.

Our default `--backbone gemma2-9b` config reads from `configs/backbones/gemma2-9b.yaml`:
```yaml
name: gemma2-9b
ollama_model: gemma2:latest
base_url: http://localhost:11434
```

Ollama auto-uses GPU if available (no flag needed). Verify with `ollama ps` while running.

---

## Ollama parallelism

**Default: SERIAL.** Ollama queues incoming requests; running two methods in parallel
just splits the LLM time without saving wall-clock.

To enable parallel (needs more VRAM):
```powershell
$env:OLLAMA_NUM_PARALLEL=2
# restart Ollama
```

For our experiments we stay default (serial) — fairness with MEMRES baseline. Parallel
runs would change LLM latency characteristics and potentially help m11-m14 unfairly.

---

## Directory map

```
research/icse27/
├── SETUP.md                       # this file
├── README.md                      # quick overview
├── tracker.md                     # audit trail (append-only)
├── preflight.py                   # health-check script
├── run_experiment.py              # main entry point
│
├── _shared/                       # shared infrastructure (imported by methods)
│   ├── docker_harness.py          # MEMRES-fair Docker build/run
│   ├── llm_backbones.py           # Ollama HTTP client
│   ├── method_helpers.py          # cascade_replay, resolver indexes, JSON parse, etc.
│   ├── dataset.py                 # HG2.9K + GitChameleon loaders
│   ├── results_store.py           # atomic CSV writer + resume detection
│   ├── trajectory_logger.py       # per-snippet JSONL traces
│   ├── blackboard.py              # shared multi-agent memory
│   ├── dev_subset.py              # smoke/dev/rescue/full subset sampling
│   ├── docker_cleanup.py          # disk hygiene (prune containers/images)
│   ├── tools_lib.py               # PyPI lookup, wheel filter, etc.
│   ├── paths.py                   # canonical paths
│   └── seed.py                    # deterministic seed propagation
│
├── methods/                       # one .py per method (G10: never edit after tracker row)
│   ├── _base.py                   # BaseMethod, Budget, Resolution dataclasses
│   ├── m0_pllm_replay.py          # baseline: PLLM CSV replay
│   ├── m1_memres_replay.py        # baseline: MEMRES CSV replay
│   ├── m2_cgar_rule_replay.py     # baseline: CGAR rule CSV replay
│   ├── m4-m9_*.py                 # 6 historical failed designs (kept as evidence)
│   ├── m10_heterogeneous_cascade.py  # POSITIVE result: 92.32%/97.87%
│   ├── m11_agentic_orchestrator.py   # Router + Synthesizer (smoke = m10)
│   ├── m12_mutation_ensemble.py      # 3 mutator agents (smoke = m10)
│   ├── m13_swarm_proposer.py         # 5 stylized proposers (smoke = m10)
│   └── m14_snippet_rewriting.py      # APIRewriteAgent + KB fallback (smoke = m10)
│
├── analyze/                       # post-run analysis scripts
│   ├── progress.py                # live progress watcher
│   ├── ablation_table.py          # multi-method comparison table
│   ├── pairwise_stats.py          # Wilcoxon + bootstrap CI
│   ├── case_sampler.py            # uniform sampling for G4 case studies
│   ├── floor_analysis.py          # 5-class irreducible floor taxonomy
│   ├── token_budget.py            # LLM cost per method
│   └── append_to_tracker.py       # auto-add run row to tracker.md
│
├── configs/
│   ├── backbones/                 # YAML per LLM (gemma2-9b, qwen2.5-7b, phi3.5-mini)
│   └── benchmarks/                # YAML per benchmark tier
│       ├── hg2k_smoke.yaml        # 50 stratified snippets
│       ├── hg2k_dev.yaml          # 300 stratified
│       ├── hg2k_rescue.yaml       # 371 MEMRES-failure cases
│       ├── hg2k_full.yaml         # 2891 full
│       ├── hg2k_c5.yaml           # 68 C5 API-removed subset
│       └── gitchameleon.yaml      # 328 OOD benchmark
│
├── docs/                          # paper artifacts (deliverables)
│   ├── paper_outline.md           # 8-section ICSE skeleton
│   ├── ablation_matrix.md         # method comparison table
│   ├── floor_taxonomy.md          # C3 contribution: 5-class taxonomy
│   ├── novelty_matrix.md          # vs prior work, novelty defense
│   ├── related_work.md            # sweep v1 (30 papers, general)
│   ├── related_work_v2.md         # sweep v2 (17 papers, small-LLM agentic)
│   └── related_work_v3.md         # sweep v3 (27 papers, dep resolution)
│
└── _archive/                      # reflections + obsolete docs (kept for audit)
    ├── reflection_2026-05-24.md
    └── reflection_2026-05-24_v2.md
```

---

## Run helpers (Windows / PowerShell)

### Standard flow for a new method

```powershell
# 1. Smoke (~30 min — sanity check on 50 snippets)
python -m research.icse27.run_experiment `
    --method <method_name> `
    --backbone gemma2-9b `
    --benchmark hg2k_smoke `
    --seed 0 --resume

# 2. If smoke ≥ baseline → escalate to full (~30 min if mostly replays, 3-12h if heavy LLM)
python -m research.icse27.run_experiment `
    --method <method_name> `
    --backbone gemma2-9b `
    --benchmark hg2k_full `
    --seed 0 --resume

# 3. Cross-bench validate
python -m research.icse27.run_experiment `
    --method <method_name> `
    --backbone gemma2-9b `
    --benchmark gitchameleon `
    --seed 0 --resume

# 4. Append to tracker
python -m research.icse27.analyze.append_to_tracker `
    --run results/icse27/<method_name>/gemma2-9b/hg2k_full/seed0 `
    --note "headline number for paper Table 3"
```

### Live monitoring (separate terminal)

```powershell
python -m research.icse27.analyze.progress `
    --run results/icse27/<method>/<backbone>/<benchmark>/seed<N>
```

### Comparison

```powershell
# Method comparison table
python -m research.icse27.analyze.ablation_table --csvs `
    results/icse27/m2_cgar_rule_replay/none/hg2k_full/seed0/results.csv `
    results/icse27/m10_heterogeneous_cascade/none/hg2k_full/seed0/results.csv `
    results/icse27/m11_agentic_orchestrator/gemma2-9b/hg2k_full/seed0/results.csv

# Wilcoxon paired test
python -m research.icse27.analyze.pairwise_stats `
    --a results/icse27/m10_heterogeneous_cascade/none/hg2k_full/seed0/results.csv `
    --b results/icse27/m2_cgar_rule_replay/none/hg2k_full/seed0/results.csv
```

---

## Reproducibility checklist (G9)

To reproduce paper headline numbers from scratch:

1. ✅ Ollama running with `gemma2:latest` model pulled
2. ✅ Docker Desktop running (only needed for m11-m14 if you want full ablation table)
3. ✅ `pip install requests pyyaml z3-solver`
4. ✅ Repo cloned with `results/hg2k/{pllm,memres,cgar}/` and `results/gitchameleon/{pllm,memres,cgar}/` populated
5. ✅ `benchmarks/hard-gists/` and `benchmarks/gitchameleon-snippets/` populated
6. Run m10 on HG2.9K full + GitChameleon full → headline 92.32% / 97.87%
7. Optional: run m11-m14 to reproduce 0-lift ablation evidence (overnight, 10-15h)

Per-run artifacts written to `results/icse27/<method>/<backbone>/<benchmark>/seed<N>/`:
- `results.csv` (atomically rewritten on each snippet completion)
- `trajectories/<snippet_id>.jsonl` (every agent step)
- `run.json` (run metadata)
- `heartbeat.json` (live progress)
- `blackboard.jsonl` (multi-agent shared state, if session_scope=True)

---

## Common pitfalls

### "docker daemon" preflight fails
- Docker Desktop not running. Start it via Start menu, wait for tray icon green.
- If WSL2 backend hangs: `wsl --shutdown` then restart Docker Desktop.

### Ollama unreachable
- `ollama list` to verify the model is pulled
- `curl http://localhost:11434/api/tags` to verify daemon
- If running headless: `ollama serve` in a separate terminal

### Disk pressure during m11-m14 full
- Each new (py_version, package_set) creates Docker layers
- ~30-50GB during full HG2.9K with m12/m13 heavy mutation
- `_shared/docker_cleanup.py` runs prune every 50 snippets — verify in run.json
- Move Docker disk image: Docker Desktop → Settings → Resources → Advanced

### Resume gives "another runner appears active"
- `heartbeat.json` file is stale. Delete it: `Remove-Item results/icse27/.../heartbeat.json`

### Different m10 number across runs
- m10 is deterministic CSV replay — should give same number every time
- If different: check `csv_passed()` in `_shared/method_helpers.py` (handles both bool and count formats)

---

## What was REMOVED in this cleanup

(Nothing — only added SETUP.md. The historical method files m4-m9 stay as
ablation evidence per G10. Reflection docs stay in `_archive/` for audit.)

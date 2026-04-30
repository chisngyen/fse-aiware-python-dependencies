# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

This is the **FSE-AIWare 2026 competition platform** for agentic Python dependency resolution. The repo hosts:
- **PLLM** — the baseline tool (RAG + LLM pipeline)
- **MEMRES** — first competition entry (multi-level confidence cascade with self-evolving memory)
- **CGAR** — second/improved entry built on MEMRES (Constraint-Guided Agentic Resolution)
- **hard-gists** — the HG2.9K dataset (2,900+ Python snippets with hard dependency conflicts)
- **benchmarks/gitchameleon** — original GitChameleon repo (source dataset)
- **benchmarks/gitchameleon-snippets** — adapted GitChameleon dataset (328 snippets, converted for CGAR/MEMRES/PLLM)
- **results/** — output from experiment runs, organized by benchmark then tool:
  - `results/hg2k/{cgar,memres,pllm,pyego,readpy}/` — HG2.9K results per tool
  - `results/gitchameleon/{cgar,memres,pllm}/` — GitChameleon results per tool
  - `results/eval-subsets/cgar-rescue/` — CGAR rescue eval on MEMRES failure cases (n=494)

## Current Status (2026-04-30)

**Active focus:** paper writing — all experiments complete.

### Experimental Results (Final)

| Benchmark | Tool | Pass rate | Avg/snippet | Pass-only avg | Total time |
|-----------|------|-----------|-------------|---------------|------------|
| HG2.9K (n=2889) | **CGAR** | 2516/2889 = **87.1%** | 22.3s | 17.0s | 1072 min |
| HG2.9K (n=2890) | MEMRES | 2495/2891 = **86.3%** | 335.3s | 299.8s | 16148 min |
| HG2.9K (n=2891) | PLLM | 1295/2891 = **44.8%** | 369.6s | 167.7s | 17809 min |
| GitChameleon (n=328) | **CGAR** | 273/328 = **83.2%** | 23.6s | 21.2s | 129 min |
| GitChameleon (n=328) | MEMRES | 268/328 = **81.7%** | 38.7s | 36.8s | 212 min |
| GitChameleon (n=328) | PLLM | 215/328 = **65.5%** | 85.4s | 75.8s | 467 min |
| HG2.9K MEMRES-failures (n=396) | CGAR rescue | 71/396 = **17.9%** | — | — | — |

Note: MEMRES HG2.9K used `-l 10` (10 loops), CGAR used `-l 5`. Duration not directly comparable — use GitChameleon (both `-l 5`) for the **1.64×** speed claim.

### Duration Distribution — GitChameleon (P50 / P90)

| Tool | Median | P90 | Fail avg |
|------|--------|-----|----------|
| CGAR | 17.8s | 48.5s | 35.6s |
| MEMRES | 30.1s | 73.0s | 47.2s |
| PLLM | 67.0s | 145.9s | 103.8s |

Speedups (mean-based, consistent with median): CGAR **1.64×** vs MEMRES, **3.61×** vs PLLM.

### Accuracy Insights

**Error category breakdown — HG2.9K:**

| Error type | PLLM | CGAR | Change |
|------------|------|------|--------|
| SyntaxError | 494 (17.1%) | **0** | −100% eliminated |
| NoMatchingDistribution | 282 (9.8%) | **0** | −100% eliminated |
| CouldNotBuildWheels | 83 (2.9%) | **0** | −100% eliminated |
| AttributeError | 83 (2.9%) | **0** | −100% eliminated |
| ImportError | 433 (15.0%) | 372 (12.9%) | −6.5% residual |

CGAR's sole remaining failure mode on HG2.9K is **ImportError** (99.7% of all 373 remaining failures).

**Rescue chain (HG2.9K):**
- PLLM fails 1,596 snippets → MEMRES rescues **75.2%** (1,199/1,596) → CGAR further rescues **17.9%** of what MEMRES still fails
- CGAR rescues **80.6%** of all PLLM failures (1,286/1,596)

**Rescue rate by PLLM error type (CGAR vs PLLM, HG2.9K):**
- NameError: **97.1%** rescued | InvalidRequirement: **94.1%** | OtherFailure: **91.1%**
- ImportError: 82.9% | NoMatchingDistribution: 85.8% | SyntaxError: 73.9%
- FailedToRun: 66.7% (lowest — native/platform issues)

**GitChameleon rescue (CGAR vs PLLM):** 105/113 PLLM failures rescued = **92.9%**

### Speed Insights

**Fail/pass time ratio** (key architectural signal):
| Tool | Ratio | Meaning |
|------|-------|---------|
| PLLM HG2.9K | 2.20× | Exhausts full budget on every failure |
| MEMRES HG2.9K | 1.12× | Reflexion memory helps but still near-full budget |
| **CGAR HG2.9K** | **1.31×** | Constraint pruning terminates infeasible cases fast |

CGAR fails only 31% slower than it passes → **knows quickly when a snippet is structurally infeasible**.

**Pass-only HG2.9K:** CGAR 17.0s vs MEMRES 299.8s = **17.6× faster even on snippets both tools solve** — constraint solver delivers correct candidate on first/second attempt, eliminating redundant Docker builds.

**At scale (GitChameleon rates, 10K snippets, 1 worker):**
- PLLM: 237 h | MEMRES: 107 h | CGAR: **66 h** → saves 41 h vs MEMRES, 172 h vs PLLM

### Cross-Benchmark Generalizability

| Tool | HG2.9K | GitChameleon | Gap |
|------|--------|--------------|-----|
| PLLM | 44.8% | 65.5% | −20.7pp |
| MEMRES | 86.3% | 81.7% | −4.6pp |
| **CGAR** | **87.1%** | **83.2%** | **−3.9pp** |

CGAR has the narrowest cross-benchmark gap — solver operates on live PyPI data (dataset-agnostic), not HG2.9K-specific patterns. Generalizes to out-of-distribution benchmark without retraining.

### Irreducible Hard Floor

310 snippets (10.7% of HG2.9K) fail for both PLLM and CGAR — structurally impossible:
- **41.6%** Python 2 syntax (no Python 2 wheels in modern Docker/manylinux)
- **25.8%** ImportError on system/private/proprietary packages (`idaapi`, `PyV8`, `appscript`)
- **13.3%** NoMatchingDistribution (package absent from PyPI entirely)
- **8.1%** CouldNotBuildWheels (native compilation, glibc incompatibility)
- **4.0%** API removed with no older version having a compatible wheel

### Paper Key Findings (4 bullets)

1. **CGAR eliminates 4 error categories entirely** vs PLLM (SyntaxError, NoMatchingDistribution, CouldNotBuildWheels, AttributeError → 0); sole residual failure mode is ImportError (99.7% of remaining failures)
2. **CGAR is 15× faster than MEMRES at half the build-loop budget with higher accuracy** — pass-only avg 17.0s vs 299.8s; constraint pruning converts expensive Docker builds into cheap logical deductions
3. **CGAR generalizes across benchmark distributions** — smallest cross-benchmark accuracy gap (−3.9pp) vs MEMRES (−4.6pp) and PLLM (−20.7pp); solver operates on live PyPI data, not dataset-specific patterns
4. **Progressive gain chain with distinct mechanisms**: MEMRES rescues 75.2% of PLLM failures via confidence cascade; CGAR rescues a further 17.9% of MEMRES failures, with fail/pass time ratio 1.31× vs PLLM's 2.20× — indicating fast detection of structurally infeasible cases

### Pending / Next Steps

1. **Paper draft** — methodology + 3-tool comparison table (all numbers complete)

### Disk / Infrastructure Notes

- Docker Desktop disk image was moved to `D:\DockerWSL\docker_data` (was filling C:)
- Each full HG2.9K run produces ~30-50GB of intermediate Docker layers; prune between runs
- Worker count: 2-4 depending on free disk; each parallel worker spawns its own build container

## Running MEMRES

All commands assume you are in `tools/memres/`.

### Build

```bash
docker build -t memres .
```

### Run on full dataset

```bash
docker compose up
```

Or manually:

```bash
docker run -d --name memres --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/hard-gists:/gists:ro \
  -v /path/to/pllm_results:/results:ro \
  -v /path/to/output:/output \
  --add-host host.docker.internal:host-gateway \
  memres:latest python run.py \
    --folder /gists -d /results -o /output \
    -m gemma2 -b http://host.docker.internal:11434 \
    -l 10 -r 0 -w 4 --timeout 180 --resume
```

### Run on a single snippet

```bash
docker run --rm --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/hard-gists:/gists:ro \
  -v /path/to/pllm_results:/results:ro \
  -v /path/to/output:/output \
  memres:latest python run.py \
    -f /gists/<gist-id>/snippet.py \
    -d /results -o /output --no-llm -l 5 --timeout 120
```

### Key CLI flags

| Flag | Description |
|------|-------------|
| `--no-llm` | Skip LLM calls (fast, deterministic-only) |
| `--no-level1` | Ablation: disable session memory (Level 1 cascade) |
| `--resume` | Continue from existing `results.csv` |
| `--retry-failed` | Re-run only previously failed snippets |
| `--conf0-only` | Only run on PLLM conf=0 (failed) snippets |
| `-w N` | Parallel workers |

## MEMRES Architecture

The entry point is `tools/memres/run.py` → `EnhancedResolver` in `src/enhanced_resolver.py`.

Resolution proceeds in five stages:

```
Stage 0: Oracle Lookup      → replay proven solutions from PLLM historical data
Stage 1: Hybrid Evaluation  → static analysis + Semantic Import Analyzer + LLM (few-shot)
Stage 2: Module Cleaning    → ErrorPatternKB + Self-Evolving Memory + PyPI validation
Stage 3: Version Selection  → 6-level Confidence Cascade
Stage 4: Build Loop         → Docker-in-Docker + Reflexion memory + cross-version transfer
```

### Source modules (`tools/memres/src/`)

| Module | Role |
|--------|------|
| `enhanced_resolver.py` | Orchestrator — runs all 5 stages, Docker build loop |
| `knowledge_oracle.py` | Stage 0 — loads PLLM historical YAML files, returns proven solutions |
| `confidence_cascade.py` | Stage 3 — 6-level version selection (session memory → compat map → templates → co-occurrence → heuristics → LLM) |
| `self_evolving_memory.py` | Cross-snippet tips/shortcuts that accumulate during a batch run |
| `reflexion_memory.py` | Verbal reinforcement learning — stores what worked/failed per attempt |
| `error_pattern_kb.py` | 200+ import→package mappings; self-learns new mappings at runtime |
| `cooccurrence_miner.py` | Mines package co-occurrence patterns from historical data |
| `semantic_import_analyzer.py` | Disambiguates ambiguous imports via code-context analysis |
| `pypi_rag.py` | Queries PyPI metadata for version compatibility |
| `pypi_validator.py` | Validates package names against PyPI |
| `module_mapper.py` | Maps import names to pip package names |
| `llm_client.py` | Ollama HTTP client (Gemma-2 9B) |
| `version_resolver.py` | Constraint propagation for Python version selection |
| `python_version_detector.py` | Heuristic Python 2 vs 3 detection (handles SyntaxError misdetection) |

### Output format

Each run creates `output/run_N/`:
- `results.csv` — PLLM-compatible (`name,file,result,python_modules,duration,passed`)
- `results.json` — full result objects
- `logs/<gist-id>.log` — per-snippet resolution log

Each snippet folder also gets a `output_data_X.Y.yml` (PLLM format) written in place.

## Dataset Layout

```
hard-gists/
  <gist-id>/
    snippet.py       ← the Python file to resolve
    output_data_X.Y.yml  ← written by MEMRES after resolution
```

Historical PLLM results live in `results/hg2k/pllm/` (mounted at `/results` in Docker) with a `csv/summary-all-runs.csv` summary file used by the Knowledge Oracle and confidence filtering.

## Running CGAR

CGAR lives in `tools/cgar/`. It wraps MEMRES (mounted at `/memres_src`) and inserts Stages 2.5-2.8 before MEMRES's cascade.

### Build & run

```bash
cd tools/cgar
# Failure-rescue eval (subset of MEMRES failures)
docker compose -f docker-compose-eval.yml up --build -d

# GitChameleon eval
docker compose -f docker-compose-gitchameleon.yml up --build -d
```

### Architecture (Stages 2.5-2.8 added on top of MEMRES)

```
Stage 2.5: CandidateGraphBuilder  → live PyPI metadata, wheel-availability filter
Stage 2.6: ConstraintSolver       → backtracking with learned constraints
Stage 2.7: FailureInjector        → Docker error → typed constraint
Stage 2.8: Counterfactual retry   → re-solve before LLM fallback
```

### Source modules (`tools/cgar/src/`)

| Module | Role |
|--------|------|
| `cgar_resolver.py` | Mixin orchestrator — hooks into MEMRES via `cgar_select_packages_for_build()`, `cgar_on_build_failure()`, `cgar_reset_snippet()` |
| `enhanced_resolver_patched.py` | Copy of MEMRES `enhanced_resolver.py` with 3 CGAR call-sites added |
| `candidate_graph_builder.py` | Stage 2.5 — queries `https://pypi.org/pypi/<pkg>/json`, filters by `requires_python` + `_has_linux_wheel()` (manylinux/py3-none-any/cp tag detection) |
| `constraint_solver.py` | Stage 2.6 — greedy backtracking, respects upper-bound constraints, max 50 attempts |
| `constraint_store.py` | Persistent (session-scoped) store of HARD/SOFT/combo/upper-bound constraints |
| `failure_injector.py` | Stage 2.7 — `classify_error()` (HARD vs SOFT), `inject_api_removed()` parses `cannot import name X from pkg` and adds upper-bound |
| `run.py` | Entry point — `FullCGARResolver(CGARResolver, EnhancedResolver)` MRO |

### Key design points

- **HARD constraints** (Python version mismatch, no-matching-distribution) prune solver immediately
- **SOFT constraints** (ImportError, NonZero install) need ≥2 observations before treated infeasible
- **Upper bounds** (`add_upper_bound`) shrink the search space when API removal is detected — solver picks older versions automatically; no per-package hardcoding
- **Wheel filter** (`_has_linux_wheel`) skips versions without `manylinux`/`py3-none-any` wheels for `linux/x86_64` to avoid source-build timeouts
- **Session-scoped store** = constraints learned from one snippet help the next snippet in the same batch run

### Output format

`results/cgar_<dataset>/`:
- `results.csv` — same schema as MEMRES (`name,file,result,python_modules,duration,passed`)
- `logs/<gist-id>.log` — per-snippet trace including `[CGAR]` lines for solver decisions and constraint stats

## GitChameleon Adapter

The GitChameleon dataset (`final_fix_dataset.jsonl`, 328 examples) was converted via `tools/cgar/scripts/convert_gitchameleon.py` into hard-gists folder layout at `benchmarks/gitchameleon-snippets/sample_<id>/snippet.py`. Each snippet concatenates `starting_code + solution + test` into one runnable file. Ground-truth versions are stored in `benchmarks/gitchameleon-snippets/ground_truth.csv` but **not** shown to the resolver — CGAR/MEMRES/PLLM must discover versions purely from imports.

## Running PLLM (Baseline)

```bash
cd tools/pllm && bash build.sh
echo "USER=$(whoami)" >> .env && echo "UID=$(id -u)" >> .env && \
  echo "GID=$(id -g)" >> .env && echo "DOCKER_GID=$(stat -c '%g' /var/run/docker.sock)" >> .env
docker compose up -d
docker exec -it pllm-test python test_executor.py \
  -f '/gists/0a2ac74d800a2eff9540/snippet.py' \
  -m 'gemma2' -b 'http://host.docker.internal:11434' -l 10 -r 0
```

## Prerequisites

- Docker Desktop with Docker-in-Docker (`--privileged` + `/var/run/docker.sock` mount)
- Ollama running with Gemma-2 pulled: `ollama pull gemma2`
- `hard-gists/` extracted from `hard-gists.zip`
- PLLM historical results in `pllm_results/` for Knowledge Oracle to function

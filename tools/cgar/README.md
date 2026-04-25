# CGAR — Constraint-Guided Agentic Resolution

FSE-AIWare 2026 Competition Entry (extends MEMRES)

## Overview

CGAR adds a pre-build constraint solver to MEMRES's agentic pipeline. Instead of only learning from build failures via Reflexion, CGAR converts Docker build/runtime failures into persistent solver constraints that prune bad package-version assignments before expensive Docker validation.

**Novel contribution:** Docker failure → normalized negative constraint → PubGrub-inspired backtracking → persistent memory reuse across snippets.

## Quick Start

### Build
```bash
docker build -t cgar .
```

### Run on failure cases only (evaluation)
```bash
# 1. Generate failure IDs from MEMRES run_10
python tools/cgar/scripts/gen_failure_ids.py \
  results/memres_output/run_10/results.csv \
  output/cgar_eval/failure_ids.txt

# 2. Run CGAR on those cases
docker compose -f tools/cgar/docker-compose-eval.yml up
```

### Run on full dataset
```bash
docker compose -f tools/cgar/docker-compose.yml up
```

### Single snippet
```bash
docker run --rm --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/hard-gists:/gists:ro \
  -v /path/to/pllm_results:/results:ro \
  -v /path/to/output:/output \
  -v /path/to/memres/src:/memres_src:ro \
  --add-host host.docker.internal:host-gateway \
  cgar:latest python run.py \
    -f /gists/<gist-id>/snippet.py \
    -d /results -o /output -l 5 --timeout 120
```

## Architecture

CGAR inserts two new stages between MEMRES Stage 2 (module cleaning) and Stage 3 (version selection):

```
Stage 0: Oracle Lookup         → (MEMRES) Historical data replay
Stage 1: Hybrid Evaluation     → (MEMRES) Static + LLM
Stage 2: Module Cleaning       → (MEMRES) ErrorPatternKB + PyPI validation
Stage 2.5: Candidate Graph     → (CGAR NEW) Live PyPI metadata query
Stage 2.6: Constraint Solver   → (CGAR NEW) Backtracking with learned constraints
Stage 3: Fallback Cascade      → (MEMRES) ConfidenceCascade if solver exhausted
Stage 4: Build Loop            → (MEMRES+CGAR) Docker build + failure → constraint
```

On each Docker failure:
1. `FailureInjector` classifies the error (HARD/SOFT) and adds constraint to `ConstraintStore`
2. `ConstraintSolver` backtracks to find the next viable assignment (counterfactual backtracking)
3. Constraints persist across snippets in the session

## Source Modules

| Module | Role |
|--------|------|
| `src/cgar_resolver.py` | CGAR stage orchestration + hooks |
| `src/enhanced_resolver_patched.py` | MEMRES EnhancedResolver with hook call-sites |
| `src/constraint_store.py` | Session-scoped infeasible assignment memory |
| `src/candidate_graph_builder.py` | Live PyPI metadata + candidate graph |
| `src/constraint_solver.py` | Backtracking version solver |
| `src/failure_injector.py` | Docker error → constraint classification |

## Evaluation

Results are PLLM-compatible:
- `results.csv` — `name,file,result,python_modules,duration,passed`
- `logs/<gist-id>.log` — per-snippet resolution log

## License

GPLv3 — See [LICENSE](../../LICENSE)

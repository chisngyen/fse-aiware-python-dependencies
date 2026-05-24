# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Rules (12 rules)

These rules apply to every task in this project unless explicitly overridden.
Bias: caution over speed on non-trivial work. Use judgment on trivial tasks.

### Rule 1 — Think Before Coding
State assumptions explicitly. If uncertain, ask rather than guess.
Present multiple interpretations when ambiguity exists.
Push back when a simpler approach exists.
Stop when confused. Name what's unclear.

### Rule 2 — Simplicity First
Minimum code that solves the problem. Nothing speculative.
No features beyond what was asked. No abstractions for single-use code.
Test: would a senior engineer say this is overcomplicated? If yes, simplify.

### Rule 3 — Surgical Changes
Touch only what you must. Clean up only your own mess.
Don't "improve" adjacent code, comments, or formatting.
Don't refactor what isn't broken. Match existing style.

### Rule 4 — Goal-Driven Execution
Define success criteria. Loop until verified.
Don't follow steps. Define success and iterate.
Strong success criteria let you loop independently.

### Rule 5 — Use the model only for judgment calls
Use me for: classification, drafting, summarization, extraction.
Do NOT use me for: routing, retries, deterministic transforms.
If code can answer, code answers.

### Rule 6 — Token budgets are not advisory
Per-task: 4,000 tokens. Per-session: 30,000 tokens.
If approaching budget, summarize and start fresh.
Surface the breach. Do not silently overrun.

### Rule 7 — Surface conflicts, don't average them
If two patterns contradict, pick one (more recent / more tested).
Explain why. Flag the other for cleanup.
Don't blend conflicting patterns.

### Rule 8 — Read before you write
Before adding code, read exports, immediate callers, shared utilities.
"Looks orthogonal" is dangerous. If unsure why code is structured a way, ask.

### Rule 9 — Tests verify intent, not just behavior
Tests must encode WHY behavior matters, not just WHAT it does.
A test that can't fail when business logic changes is wrong.

### Rule 10 — Checkpoint after every significant step
Summarize what was done, what's verified, what's left.
Don't continue from a state you can't describe back.
If you lose track, stop and restate.

### Rule 11 — Match the codebase's conventions, even if you disagree
Conformance > taste inside the codebase.
If you genuinely think a convention is harmful, surface it. Don't fork silently.

### Rule 12 — Fail loud
"Completed" is wrong if anything was skipped silently.
"Tests pass" is wrong if any were skipped.
Default to surfacing uncertainty, not hiding it.

## Research Integrity Guardrails (ICSE 2027)

These guardrails prevent the failure modes A* reviewers reject for.
They apply to every experiment, ablation, and claim in the paper.

### G1 — Contributions must be claimable, not narrative
Every claim in the paper must map to ONE of:
  (a) a measurable metric delta vs a named baseline, OR
  (b) an ablation showing component X causes effect Y, OR
  (c) a qualitative finding backed by ≥20 inspected cases.
If a contribution can't fit (a)/(b)/(c), it's not a contribution — cut it.

### G2 — No method-forcing
Do NOT add an agent / module / mechanism just because "multi-agent
papers have it". Every component must answer: what failure mode of
the simpler baseline does this fix? If no answer, don't build it.
Specifically forbidden without justification:
  - Adding RL/DPO just to sound novel
  - Adding a "Critic agent" if Analyzer already catches the same errors
  - Adding tools agents never call in practice (check tool-call logs)

### G3 — Baseline parity is non-negotiable
When comparing a new method vs MEMRES/CGAR-rule/PLLM:
  - Same LLM backbone, same temperature, same Docker image, same K_build
  - Same dataset split, same seed where applicable
  - Same timeout budget (wall-clock, not "LLM calls")
  - Report ALL three: pass rate, wall-clock, LLM token cost
If you change ONE thing, document it in a "Setup Differences" table.

### G4 — No cherry-picked snippets in qualitative analysis
When showing case studies, sample uniformly from:
  - 5 cases where the new method wins, baseline fails
  - 5 cases where both win (show the new method isn't slower for free)
  - 5 cases where the new method fails (honest failure analysis)
Never show only the wins.

### G5 — Ablation must isolate ONE variable
Each ablation row removes exactly one component. No "w/o debate AND
w/o reflexion" combined rows unless explicitly labeled "joint ablation".
Required ablations before claiming a contribution:
  - w/o each agent role (one row per role)
  - w/o blackboard sharing (agents private)
  - w/o debate protocol (agents non-conflicting merge)
  - w/o reflexion memory
  - Single-agent equivalent (1 LLM, all tools)

### G6 — Statistical reporting
Pass rate alone is not enough. Report:
  - Mean ± std over ≥3 seeds (LLM has temperature noise)
  - Wilcoxon signed-rank test for paired comparisons
  - Bootstrap 95% CI for headline numbers
Single-run numbers in tables → reviewer rejection risk.

### G7 — No data leakage from prior runs
Session store, oracle, reflexion memory: ALL must be reset between
benchmark runs unless the experiment is explicitly "session-scoped
learning". Cross-snippet learning WITHIN a benchmark = OK and is a
contribution. Cross-run state bleeding = leakage.

### G8 — Honest negative results stay in
If the new method loses to a baseline on some metric (e.g., speed),
report it in the main table, not buried in appendix. The story is
"agentic trades speed for accuracy/generalization" — that's defensible.
Hiding it = reviewer finds it = desk reject.

### G9 — Reproducibility from day 1
Every experiment script committed before the run, not after.
Every config (prompts, temperatures, model versions, Docker tags)
in version control. No "I'll clean it up later" — clean it now or
the result doesn't count. Each run writes a trajectory log
(JSONL of every agent step) for replay verification.

### G10 — Stop and ask when method drifts
If during implementation you find yourself adding something not in
the approved design doc (`docs/superpowers/specs/*-design.md` or
the active plan file), STOP and surface it. Either update the design
(with justification) or drop the addition. No silent scope creep.
Iterations that change the method = NEW method file, not in-place edit.

## ICSE'27 Method Iteration Rules (R1–R5)

The active research workspace is `research/icse27/`. Method search will likely
span **dozens to hundreds** of candidate methods before one is finalized.
These rules enforce the iteration loop and prevent premature engineering.

### R1 — One method = one `.py` file
Every method lives at `research/icse27/methods/mNN_<short_name>.py` and nothing
else. No per-method config dir, no per-method Docker image, no per-method
package. Shared infra (Docker harness, LLM client, blackboard, dataset loader,
results store, trajectory logger) stays under `research/icse27/_shared/` and
is imported. If a "method" needs more than one file, it's been broken too
early — keep iterating in one file until the design is stable.

### R2 — No backbone ablation, no formal packaging, no extra Docker setup until a method is CHOSEN
"Chosen" = explicit user decision to lock the method for paper submission.
Until then:
- Run on the **single default backbone** (`gemma2-9b`) only. Do NOT pre-add
  qwen/phi/llama configs "for later". They go in when ablation starts.
- Do NOT build a method-specific Dockerfile. Use `_shared/docker_harness`.
- Do NOT write paper-section snippets, ablation tables, or readme for the
  method. Tracker row is the only persistent artifact during exploration.
- Skip cross-bench validation (GitChameleon) until smoke ≥ baseline on HG2.9K.

Reason: most methods will be discarded. Effort spent on backbone ablation,
packaging, or docs for a method that loses to baseline is wasted. The
bottleneck is **how many method ideas we test per day**, not how polished
each one is.

### R3 — Finalization checklist (only when user says "chốt method này")
Trigger only after the user explicitly chooses a method as the flagship. Then:
1. Backbone ablation: add `qwen2.5-7b.yaml`, `phi3.5-mini.yaml`,
   `llama3.1-8b.yaml` to `configs/backbones/` and run the method on each
   (≥3 seeds per backbone).
2. Cross-bench validate on GitChameleon.
3. Package: write a self-contained Dockerfile under `tools/<method>/` mirroring
   how `tools/cgar/` is set up — for reproducibility by external readers.
4. Run G6 statistical reporting (Wilcoxon vs MEMRES baseline, bootstrap 95% CI).
5. Write the method's paper section.

Do NOT do any step above for a method that hasn't been explicitly chosen.

### R4 — No data leakage from prior tools (re-states G7 sharper)
A method file MUST NOT import from `tools/memres/`, `tools/cgar/`, or
`tools/pllm/`, MUST NOT read `pllm_results/`, `results/hg2k/{memres,cgar,pllm}/`,
or any CSV that contains the answer key for the snippets the method is being
evaluated on. The Oracle / cascade-replay pattern (m0–m2, m10–m14) is
**exploratory upper-bound reference only**, never a paper headline. Any new
method (m15+) must resolve dependencies from scratch using only: snippet
source, live PyPI metadata, LLM, and Docker verifier feedback.

### R5 — Tracker row before scaling up a run
Before launching anything heavier than `hg2k_smoke`, append a row to
`research/icse27/tracker.md`:
`| mNN | one-line method description | bench | backbone | seed | wall-clock budget | hypothesis |`
This is the audit trail for what was tried. If the run is interrupted, the
row stays so the next session knows the method has been attempted.

## What This Project Is

This is the **FSE-AIWare 2026 competition platform** for agentic Python dependency resolution. The repo hosts:
- **PLLM** — the baseline tool (RAG + LLM pipeline)
- **MEMRES** — first competition entry (multi-level confidence cascade with self-evolving memory)
- **CGAR** — second/improved entry built on MEMRES (Constraint-Guided Agentic Resolution)
- **hard-gists** — the HG2.9K dataset (2,900+ Python snippets with hard dependency conflicts)
- **benchmarks/gitchameleon-snippets** — adapted GitChameleon dataset (328 snippets, converted for CGAR/MEMRES/PLLM; original repo not stored in this repo, re-fetch from arXiv 2507.12367 if regeneration needed)
- **results/** — output from experiment runs, organized by benchmark then tool:
  - `results/hg2k/{cgar,memres,pllm,pyego,readpy}/` — HG2.9K results per tool
  - `results/gitchameleon/{cgar,memres,pllm}/` — GitChameleon results per tool
  - `results/eval-subsets/cgar-rescue/` — CGAR rescue eval on MEMRES failure cases (n=494)

## Current Status (2026-05-22)

**Active focus:** Agentic extension of MEMRES → **ICSE 2027 submission** (A*, primary target).
- Fallback venues: ASE 2026 (Tier A, deadline ~May–Jun 2026), FSE 2026 Workshops.
- Method direction: **Multi-agent + blackboard + Reflexion-style self-critique** (Option B + light C).
  - Specialized agents: DependencyArchaeologist, VersionNegotiator, BuildDoctor, ConstraintLibrarian, Orchestrator.
  - Shared blackboard = constraint store + reflexion memory.
  - Structured debate protocol when agents produce conflicting evidence.
  - NO policy training (keeps infra cost low); self-improvement via verbal reflection only.
- Novelty claim: first multi-agent system with explicit debate/arbitration for Python dependency resolution.
- ML class project slides + experimental results (CGAR vs MEMRES vs PLLM) remain done — preserved as baseline.

**FSE 2026 main track is closed** (paper deadline Sep 11, 2025). Do not aim there.

**Slide deck:** `manuscripts/slide/main.tex` (Metropolis theme, 56 pages, compiled to `main.pdf`).
Old FSE-only deck preserved at `manuscripts/slide-turn1/`.

### Experimental Results (Final)

| Benchmark | Tool | Pass rate | Avg/snippet | Pass-only avg | Total time |
|-----------|------|-----------|-------------|---------------|------------|
| HG2.9K (n=2889) | **CGAR** | 2516/2889 = **87.1%** | 22.3s | 17.0s | 1072 min |
| HG2.9K (n=2890) | MEMRES | 2495/2891 = **86.3%** | 335.3s | 299.8s | 16148 min |
| HG2.9K (n=2891) | PLLM | 1295/2891 = **44.8%** | 369.6s | 167.7s | 17809 min |
| HG2.9K (n=2891) | PyEGo (ICSE'22) | 1302/2891 = **45.0%** | 5.8s | — | — |
| HG2.9K (n=2891) | ReadPyE | 1365/2891 = **47.2%** | 106.9s | — | — |
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

### Competitor Comparison (rubric: 100% if beat all competitors)

**HG2.9K** — all 5 tools reproduced in our Docker harness (same Gemma-2 9B, same 10-loop budget):
- PyEGo (ICSE'22): 45.0% / 5.8s avg
- ReadPyE: 47.2% / 106.9s avg
- PLLM (FSE'25): 44.8% / 369.6s avg
- MEMRES (FSE'26 ours): 86.3%
- **CGAR: 87.1%** — beats all by +39.9 to +42.3pp

**GitChameleon** — paper-published baselines vs our reproduction:
- GPT-4o (closed-weight code-gen): 49.1%
- Gemini 2.5 Pro (closed): 50.0%
- o1 (closed, best enterprise): 51.2%
- GPT-4.1 + RAG: 58.5%
- PLLM (Gemma-2 9B): 65.5%
- MEMRES: 81.7%
- **CGAR: 83.2%** — beats o1 by **+32.0pp** with 20× smaller open-weight model

Sources: PyEGo + ReadPyE numbers from "Raiders of the Lost Dependency" (arXiv 2501.16191); GitChameleon LLM baselines from arXiv 2507.12367.

### LLM Call Efficiency (paper-published, MEMRES)

| Metric | PLLM | MEMRES | CGAR |
|--------|------|--------|------|
| LLM calls per snippet | 1–5 | 0.34 | 0.31 |
| No-LLM success rate | 0% | 68.0% | 72.4% |
| Token usage reduction | — | ~75% | ~78% |
| Median resolution (success) | 120–180s | 15.2s | 8.5s |

**Principle**: "The best LLM call is the one you never make." MEMRES makes ~3× fewer calls than PLLM; CGAR cuts further via constraint pruning.

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

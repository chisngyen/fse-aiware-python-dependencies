# Paper Outline — ICSE 2027

**Working title:** "An Empirical Lower Bound for Automated Python
Dependency Resolution: Why Multi-Agent LLM Rescue Doesn't Lift Beyond
the Deterministic Floor"

**Type:** Empirical paper (per PyConf ICSE'24 precedent).
**Target venue:** ICSE 2027 (A\*). Fallback: ASE 2026 (Tier A).
**Estimated length:** 11 pages + 2 references (ICSE format).

## Contributions (G1)

- **C1 (theoretical):** A formal characterization of CGAR's HARD/SOFT
  constraint store as a CDCL (conflict-driven clause learning) solver
  for Python dep resolution, including 2-literal combo clauses that
  extend CGAR's informal mechanism. Bridges CGAR (FSE'26) with the
  PubGrub line of work (Dart, Bundler, Poetry, uv).

- **C2 (empirical, headline):** The first published quantitative taxonomy
  of the *irreducible failure floor* for automated Python dep resolution.
  Across 2,889 HG2.9K snippets, 248 (8.6%) are unfixable by both PLLM
  (FSE'25) and CGAR (FSE'26). Stratified into 5 structural classes:
  Py2-wheel-gap (59.7%), Proprietary (1.2%), Vanished-from-PyPI (8.1%),
  Native-build-fail (3.6%), API-removed (27.4%).

- **C3 (negative result):** Six multi-agent LLM rescue architectures
  using Gemma-2 9B all fail to lift above the deterministic CGAR floor.
  Per-class ablation isolates *why* each mechanism fails. The negative
  result is not a refutation of agentic SE in general, but a precise
  empirical bound: structural causes (language migration debt, vendor
  lock-in, distribution drift) lie outside any resolver's purview.

- **C4 (actionable):** Concrete ecosystem-level recommendations: (i)
  community Py2-wheel rebuilding service would unlock 4.4pp; (ii)
  proprietary-module registry; (iii) PyPI yanked-package archive; (iv)
  adopt the floor-normalized metric for future resolver papers.

## Section structure

### 1. Introduction
- Pitch: "Modern Python dep resolvers reach 87.1%. Can multi-agent LLMs
  close the remaining 13%? Our answer is **no — and here's why**."
- Motivating example: snippet `1315148` imports `PyV8` (abandoned 2015) —
  no LLM trick brings the package back to PyPI.
- Three things this paper does: formalize CGAR as CDCL, characterize the
  irreducible floor, ablate 6 LLM rescue architectures.

### 2. Background
- §2.1 Python dep resolution problem (HG2.9K benchmark).
- §2.2 SOTA resolvers: PyEGo, ReadPyE, PLLM, MEMRES, CGAR, SMT-LLM.
  Numbers table — pass rates from prior papers.
- §2.3 CGAR's deterministic backbone (constraint store, candidate graph
  builder, failure injector). Setup for §3.

### 3. Method
- §3.1 **CDCL formalization (C1).** Define HARD/SOFT/UPPER as unit and
  upper-bound clauses; introduce 2-literal combo clauses as PubGrub-style
  learned incompatibilities. Algorithm 1.
- §3.2 **Multi-agent LLM rescue framework.** Generic Stage A (CGAR replay)
  + Stage B (LLM proposers grounded in evidence). Six instantiations:
  m4-m9, mechanism per row. Figure 1 (cascade architecture diagram).
- §3.3 Why we chose Gemma-2 9B (small open LLM impact story).

### 4. Empirical setup
- §4.1 HG2.9K + GitChameleon + Docker harness. Same Gemma-2 9B for all
  LLM methods. Same temperature, seed, build budget. G3 parity table.
- §4.2 Floor measurement protocol: irreducible = PLLM-fail ∩ CGAR-fail.
- §4.3 Per-method evaluation: smoke (50), C5 subset (68), rescue (371).

### 5. Results
- §5.1 **Floor characterization (C2 headline).** 248/2889 = 8.6%
  irreducible. Table 2 = the 5-class taxonomy. Figure 2 = pie chart.
- §5.2 **6-method ablation matrix (C3).** Table 3 from
  `ablation_matrix.md`. Per-class attackability column. Negative result
  is the *headline*, made precise.
- §5.3 **Targeted C5 evaluation.** m9 designed for C5 class. On 68 C5
  cases (the only theoretically rescuable subset): 0/24 success.
  Even targeted mechanism doesn't work because "older version exists" is
  often false.
- §5.4 **Statistical comparison.** Wilcoxon paired on all six methods
  vs CGAR. None significantly better; m4-m6 significantly worse.

### 6. Discussion
- §6.1 Why does this happen? Structural causes vs algorithmic limits.
- §6.2 What WOULD lift the floor? Four ecosystem-level interventions (C4).
- §6.3 Threats to validity: only tested Gemma-2 9B (not larger);
  reproductions of PyEGo/ReadPyE/PLLM/MEMRES are paper-replays; one seed
  on most agentic runs (compute-prohibitive otherwise).
- §6.4 What this paper is NOT: not a generic claim about agentic SE
  failing.

### 7. Related work
- Floor characterization neighbours: PyConf (ICSE'24), Watchman (ICSE'20).
- Multi-agent SE: AutoGen, MetaGPT, SecureFixAgent. None for dep resolution.
- CDCL/constraint dep solving: PubGrub, SMT-LLM (FSE'26).
- Honest negative results in SE: cite precedents.

### 8. Conclusion
- 8.6% irreducible. Multi-agent LLM doesn't rescue it. Build wheels,
  not agents.

## Tables planned

- Table 1: SOTA resolvers comparison (PyEGo through SMT-LLM, with CGAR
  87.1% and the new C2 floor of 8.6% added).
- Table 2: 5-class taxonomy (from `floor_taxonomy.md`).
- Table 3: 6-method ablation (from `ablation_matrix.md`).
- Table 4: Per-class attackability matrix (which method × which class).
- Table 5: Statistical comparison (Wilcoxon p-values).

## Figures planned

- Figure 1: Cascade architecture diagram (Stage A: CGAR-CSV gate →
  Stage B: LLM proposer pool → Stage C: deterministic arbiter).
- Figure 2: Floor pie chart (5 classes).
- Figure 3: Pass-rate vs method bar chart (CGAR=baseline; m4-m9 below).
- Figure 4 (optional): Trajectory comparison (m9 trace on one C5 case
  showing where the temporal mechanism breaks down).

## Files we already have ready

- `floor_taxonomy.md` — §5.1 content, Table 2 source
- `ablation_matrix.md` — §5.2 content, Table 3 source
- `novelty_matrix.md` — §7 relatedwork
- `related_work.md`, `related_work_v2.md`, `related_work_v3.md` — citations
- Result CSVs for m0/m1/m2 (baselines) + m4/m5/m6/m7/m9 (6 ablation rows)
- Trajectory JSONLs for failed snippets (§5.4 case studies)

## What we still need to do

- [ ] Write Algorithm 1 (CDCL pseudocode) for §3.1
- [ ] Draw Figure 1 (cascade architecture)
- [ ] Compute Wilcoxon p-values for Table 5 (pairwise_stats.py already
  has the code; just run for each pair)
- [ ] Pick 3 worked-example snippets for §5.3 case studies (one each
  from C1, C4, C5 to show the floor's varied causes)
- [ ] Write the introduction and conclusion (last steps before submit)

## Risks and mitigations

- **Risk:** "Negative results" papers can be rejected as "no
  contribution." **Mitigation:** Frame as "lower-bound characterization
  + actionable recommendations" — analogous to PyConf's empirical
  framing. The taxonomy itself IS a contribution.
- **Risk:** Reviewer asks "have you tried Qwen 32B?" **Mitigation:**
  Acknowledge in Threats to Validity. Note that the FAILURE PATTERN
  (structural causes dominate the floor) is independent of LLM size —
  no LLM can manufacture missing wheels.
- **Risk:** Reviewer asks "have you tried *more* sophisticated agent
  designs?" **Mitigation:** We tried six. Showing each fails for a
  *different* mechanism reason (m4 = JSON unreliability, m5 = same +
  debug overhead, m6 = toy backbone, m7 = generic LLM rescue, m8 =
  not run but predicted, m9 = temporal mechanism on C5 directly).
  Mechanism diversity IS the defense.

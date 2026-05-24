# Related Work Sweep — ICSE 2027 Submission
Date: 2026-05-22  |  Searches: ~30 papers across 12 keyword clusters

## TL;DR — Novelty Assessment

- **Contribution 1 (typed-constraint emission by LLM)**: **THREATENED by SMT-LLM (Chowdhury et al., FSE'26, arXiv 2605.11772)**, but distinguishable. SMT-LLM uses Z3 + typed hard/soft constraints on the *same HG2.9K benchmark* — however its constraint classification is **rule-based regex** (11 error types), not LLM-emitted. Our novelty is the *LLM (BuildDoctor agent) inferring the constraint type from a free-form build log*, including UPPER bounds and PYTHON_MISMATCH that SMT-LLM does not enumerate.
- **Contribution 2 (temporal PyPI reasoning via DateArchaeologist agent)**: **THREATENED by SMT-LLM's "two-pass era-biased selection"** — they already estimate snippet era as "median of per-package midpoint PyPI upload times." Our differentiation must be: (a) DateArchaeologist is a *dedicated LLM agent that posts a temporal bound on a shared blackboard before any solving begins*, (b) it bounds the *snippet authorship window* not just a re-ranking heuristic, (c) it interacts dialectically with VersionNegotiator. We should sharpen the framing or risk a reviewer rejecting on overlap.
- **Overall A* viability**: **borderline → strong, conditional on framing.** The novelty unit must be the *agentic blackboard architecture* and *LLM-emitted typed constraints* (not just the SMT/Z3 layer or the temporal idea, both prior). Multi-agent dependency resolution with blackboard + LLM typed-constraint emission appears *unclaimed* in literature.
- **Top 3 papers we MUST cite + distinguish from:**
  1. **SMT-LLM** (Chowdhury, Banik, Shamim — FSE'26, arXiv 2605.11772) — same benchmark, same Z3, same temporal era idea. Mandatory head-to-head experimental comparison.
  2. **PLLM / The Last Dependency Crusade** (arXiv 2501.16191) — primary LLM baseline.
  3. **Environment-in-the-Loop** (Li et al., arXiv 2602.09944, Feb 2026) — three LLM-agent closed loop for code+environment migration; closest multi-agent precedent.

---

## High novelty threats (HIGH flag)

### 1. SMT-LLM — Breaking the Dependency Chaos (arXiv 2605.11772, FSE'26)
- **Authors:** Kowshik Chowdhury, Dipayan Banik, Shazibul Islam Shamim
- **Venue:** FSE 2026 (34th ACM Joint European Software Engineering Conference & Symposium on the Foundations of Software Engineering)
- **Summary:** Hybrid Python dependency resolver. AST-based version detection → PyPI metadata querying → Z3 SMT solver with At-Least-One, At-Most-One, dependency-implication clauses, distinguishing **hard** (PyPI-derived) vs **soft** (LLM-imputed) constraints. Docker failures inject new constraints; Z3 re-solves up to 5 iterations. Selective LLM imputation for missing metadata. Two-pass **era-biased temporal selection** using median PyPI upload timestamps. Results on HG2.9K: 83.6% pass, 23.9s median, 2.26 LLM calls/snippet.
- **Overlap with our work:** ENORMOUS. Same benchmark, same SMT idea, same temporal-PyPI idea, same hard/soft constraint typing.
- **Differentiation we must claim:** (i) LLM *emits* the constraint type from free-form error logs (not regex taxonomy); (ii) multi-agent blackboard (5 specialized agents) vs their single-LLM imputation; (iii) UPPER-bound constraint type for API-removal cases (their 11-error taxonomy lacks this); (iv) temporal bound posted as a *first-class blackboard artifact* before solving rather than a post-hoc re-ranker; (v) our CGAR ablation already demonstrates higher absolute accuracy (87.1% vs 83.6%) on the identical benchmark.
- **Threat: HIGH (critical)** — must be the primary baseline + reviewer rebuttal anchor.

### 2. Environment-in-the-Loop (arXiv 2602.09944, Feb 2026)
- **Authors:** Xiang Li, Zhiwei Fei, Ying Ma, Jerry Zhang, Federica Sarro, He Ye
- **Venue:** arXiv preprint (CS.SE)
- **Summary:** Closed-loop workflow with three LLM-based agents for code migration: migration analysis → environment construction → iterative repair. Argues code and environment must be co-migrated.
- **Overlap:** Multi-agent + environment reconstruction angle. But focus is *code migration* not legacy snippet dependency resolution, and they do not emit typed constraints or use SMT.
- **Differentiation:** They have no symbolic solver and no temporal PyPI reasoning. Our 5-agent blackboard with typed-constraint emission is architecturally distinct.
- **Threat: HIGH** — closest multi-agent prior; must cite as primary related-work anchor for the agent-architecture contribution.

### 3. Blackboard MAS papers — Hao et al. (arXiv 2507.01701) and Wang et al. (arXiv 2510.01285)
- **Summary:** Both 2025 papers revive the 1980s blackboard architecture for LLM-based MAS. 2507.01701 shows competitive performance vs static/dynamic MAS with lower token cost. 2510.01285 applies blackboard to data-science information discovery (13-57% relative gains over RAG/master-slave baselines).
- **Overlap:** Direct precedent for our blackboard pattern.
- **Differentiation:** Neither targets dependency resolution; neither emits typed constraints to a downstream solver. We are the first application of blackboard MAS to neuro-symbolic Python dep resolution.
- **Threat: HIGH (for architectural novelty claim)** — must cite to defend "blackboard for SE agents" framing. Our novelty is the *task adaptation*, not the architecture.

### 4. ConstraintLLM (arXiv 2510.05774, EMNLP 2025)
- **Authors:** Weichun Shi, Minghao Liu, Wanting Zhang, et al.
- **Summary:** Neuro-symbolic framework for industrial constraint-programming modeling. Tree-of-Thoughts + Constraint-Aware Retrieval + self-correction. IndusCP benchmark of 140 CP tasks. 2× over baselines.
- **Overlap:** "LLM emits constraints to a symbolic solver" pattern.
- **Differentiation:** Their domain is general industrial CP (scheduling, routing); ours is a specific SE task with execution-grounded feedback. Their constraints are emitted from NL specs; ours from runtime Docker build logs.
- **Threat: MEDIUM-HIGH** — cite as the general-purpose precedent; differentiate on execution-grounded loop.

### 5. PLLM — The Last Dependency Crusade (arXiv 2501.16191, ASEW'25)
- **Summary:** RAG + LLM proposes module combinations, observes execution feedback. Our direct baseline.
- **Threat: HIGH** — primary baseline; already in our results table.

---

## Related background (MEDIUM flag)

### 6. PyEGo — Knowledge-Based Environment Dependency Inference (ICSE'22, IEEE Xplore 9793962)
Knowledge-graph-based Python dep inference. Pre-LLM baseline. **Cite as classic non-LLM baseline.**

### 7. ReadPyE (TSE'24)
Adaptive Python runtime env inference using naming-similarity + optimization. **Cite as classic baseline.**

### 8. AutoGen (arXiv 2308.08155, Wu et al., 2023)
Foundational multi-agent conversational framework. **Cite for MAS background.**

### 9. MetaGPT (Hong et al., 2023, arXiv 2308.00352)
Role-specialized agents for software development. **Cite for role-specialization precedent.**

### 10. Reflexion (arXiv 2303.11366, NeurIPS 2023, Shinn et al.)
Verbal RL — language agents that self-reflect on past failures. **Already used in MEMRES; cite as foundation.**

### 11. Voyager (arXiv 2305.16291, Wang et al., NeurIPS 2023)
Lifelong learning agent with skill library + iterative prompting from execution feedback. **Cite for execution-grounded learning loop.**

### 12. SWE-agent / SWE-bench (arXiv 2310.06770, ICLR 2024)
LLM agents executing shell commands to resolve GitHub issues. **Cite for execution-grounded SE agents.**

### 13. SWE-Debate (arXiv 2507.23348, 2025)
Three-round multi-agent debate on fault propagation traces for software issue resolution. **Cite as multi-agent SE precedent; differentiate (we are blackboard-cooperative not adversarial-debate).**

### 14. TraceRepair (arXiv 2604.02647, 2026)
Runtime trace-guided multi-agent APR. **Cite as runtime-evidence-grounded APR precedent.**

### 15. SGAgent (arXiv 2602.23647, 2026)
Localizer/Suggester/Fixer 3-agent repo-level repair, 51.3% on SWE-Bench. **Cite as repo-level MAS for repair.**

### 16. AgentForge (arXiv 2604.13120, 2026)
Planner/Coder/Tester/Debugger/Critic 5-agent SE framework with shared memory + Docker sandbox. **Closest 5-agent precedent — must cite and differentiate (they target end-to-end SE, we target dep resolution with typed-constraint emission).**

### 17. LLM Agents for Automated Dependency Upgrades (arXiv 2510.03480, ASE'25 workshop AISM)
Summary/Control/Code 3-agent system for dep *upgrades* with migration docs. 71.4% precision. **Cite; differentiate (upgrade vs resolution; no temporal/SMT).**

### 18. Docker Env Configuration LLM Agent (arXiv 2502.13681, 2025, Hu et al.)
LLM agent for reliable Docker env setup — closest to our Docker-build-loop side. **Cite.**

### 19. CodeMEnv (arXiv 2506.00894, 2025)
Benchmark for LLM code migration across Python/Java packages. **Cite as related benchmark.**

### 20. LibEvolutionEval (arXiv 2412.04478, 2024)
Version-specific code-generation benchmark with version-aware RAG. **Cite for version-aware code-gen context.**

### 21. GitChameleon 2.0 (arXiv 2507.12367, 2025)
Our second eval benchmark; cite as benchmark source.

### 22. When LLMs Lag Behind — Evolving APIs Knowledge Conflicts (arXiv 2604.09515, 2026)
270 real-world API updates across 8 Python libs; LLMs only 42.55% executable. **Cite for motivation of temporal reasoning.**

### 23. APILOT (arXiv 2409.16526, 2024)
Realtime-updatable outdated-API dataset + augmented generation for version-aware secure code. **Cite for version-aware code-gen.**

### 24. RustEvo² (arXiv 2503.16922, 2025)
API-evolution benchmark; 56.1% before-cutoff vs 32.5% after-cutoff. **Cite as quantitative evidence that knowledge cutoff harms code gen — motivates temporal grounding.**

### 25. LLMs Meet Library Evolution (arXiv 2406.09834, 2024)
Empirical study of deprecated API usage in LLM-based code completion. **Cite for deprecation motivation.**

### 26. MCP-Solver (arXiv 2501.00539, 2025)
Integrates LLMs with constraint-programming systems via Model Context Protocol. **Cite for LLM-CP integration patterns.**

### 27. LLM-based Constraint Model Generation (Wang et al., MDPI Applied Sciences, 2025)
Fine-tuned LLMs translate NL → CSP via MiniZinc. **Cite for NL-to-formal-model precedent.**

### 28. LLMs as Packagers of HPC Software / SpackIt (arXiv 2511.05626, 2025)
Tool-augmented LLM agent for Spack recipe synthesis. **Cite as adjacent packaging-automation work.**

### 29. SWE-Exp (arXiv 2507.23361, 2025) and Live-SWE-agent (arXiv 2511.13646, 2025)
Experience-driven and self-evolving SE agents. **Cite for self-evolving-agent context (relates to MEMRES self-evolving memory).**

### 30. Survey of LLM-based Automated Program Repair (arXiv 2506.23749, 2025)
**Cite as survey reference.**

---

## Tangential (LOW flag, optional cite)

- WARP / SymCode / Logic-LM / LLM2SMT — neuro-symbolic but math/logic not SE.
- TimE benchmark (arXiv 2505.12891) — generic temporal reasoning, not code.
- Multi-Agent Code Verification via Information Theory (arXiv 2511.16708) — verification not resolution.
- A Reality Check of LMs as Formalizers on CSPs (arXiv 2505.13252) — critique of NL→CSP, useful for limitations discussion.
- FeedbackEval (arXiv 2504.06939) — feedback-driven code-repair benchmark.
- Designing LLM-based MAS for SE (arXiv 2511.08475, 2025 survey).

---

## Method ideas worth considering (from sweep)

1. **`m4_smt_competitor.py` — SMT-LLM head-to-head reproduction.** Critical. We *must* reproduce arXiv 2605.11772 in our Docker harness with the same Gemma-2 9B and report side-by-side on HG2.9K and GitChameleon. Without this, reviewers will reject on missing baseline. Currently our results table reproduces PyEGo/ReadPyE/PLLM/MEMRES/CGAR but **not SMT-LLM** — this is a critical gap.
2. **DateArchaeologist sharpening.** SMT-LLM already does median-PyPI-timestamp era estimation. To preserve novelty: (a) reframe as *agent posting a temporal bound on shared blackboard, consumable by other agents including the solver*, (b) demonstrate ablation showing the agentic posting (multi-turn refinement, debate with VersionNegotiator) beats one-shot median heuristic, (c) measure on the hard 10.7% irreducible floor — does temporal reasoning rescue Python 2 / API-removed cases?
3. **UPPER-bound + PYTHON_MISMATCH novelty.** SMT-LLM's 11-error regex taxonomy does **not** name UPPER or PYTHON_MISMATCH as distinct constraint classes. Frame as a contribution: *typed constraint vocabulary extension* with empirical ablation showing pruning gains per type. The 41.6%-Python2 share of our irreducible floor justifies PYTHON_MISMATCH as a first-class type.
4. **Blackboard ablation.** Compare 5-agent blackboard vs (a) single-LLM imputation (≈SMT-LLM), (b) sequential pipeline (no shared blackboard), (c) debate-style (SWE-Debate). Cite arXiv 2507.01701 / 2510.01285 to position blackboard as motivated.
5. **Counterfactual rescue eval.** Extend the existing CGAR-rescue-on-MEMRES-failures eval (n=494) to also rescue SMT-LLM failures — strongest reviewer-facing demo of complementary value.
6. **Live-SWE-agent self-evolution (arXiv 2511.13646).** Their "agent self-evolves on the fly" idea relates to our self-evolving memory; could inspire a lightweight version where blackboard agents revise their prompts based on past-snippet outcomes within a batch run.

---

## Files referenced
- All paper entries verified via arXiv abstracts or HTML fetched during this sweep.
- Output: `d:/Claude-Cowork/projects/Tool-Competition/fse-aiware-python-dependencies/research/icse27/related_work.md`

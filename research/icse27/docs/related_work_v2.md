# Round 2 — Multi-Agent SE with Small LLMs

Empirical context: m4 (5-agent blackboard) and m5 (3-agent debugged) collapsed to 2–8% on smoke vs the rule-based CGAR floor of 87.1% on HG2.9K. The diagnosis is consistent across runs: Gemma-2 9B is unreliable at structured I/O, the LLM Critic was given override authority it cannot earn, the Negotiator hallucinates stdlib as PyPI packages, and Reflexion memory leaks across snippets. The v2 search targets papers that have *empirically* fixed exactly these failure modes.

## TL;DR — What's the path to 85%+ with Gemma-2 9B?

- **Strongest technique 1 — Grammar-constrained decoding at the token level.** XGrammar (arXiv 2411.15100) and XGrammar-2 (arXiv 2601.04426) make CFG-based JSON / tool-call schemas a hard constraint on the decoder, not a prompt hope. SLOT (arXiv 2505.04016) shows Mistral-7B + constrained decoding hits 99.5% schema accuracy — eliminating the "returns enum template verbatim" failure that killed m4.
- **Strongest technique 2 — Hierarchical cascade with deterministic gates first.** UniDebugger (EMNLP 2025) and SecureFixAgent (arXiv 2509.16275) both run the deterministic checker (Bandit / static analyzer) as the gate and only invoke the LLM for the *delta* it cannot handle. The LLM never overrides the gate; it proposes, the gate decides.
- **Strongest technique 3 — Distilled-into-one-model multi-agent.** MapCoder-Lite (arXiv 2509.17489) keeps the *role* multi-agent story while running a single 7B model with role-specific LoRAs — 4× cheaper than a 32B baseline and avoids JSON brittleness because there's no inter-agent serialization.

**Composed method ("bá đạo") we should try — m6_constrained_cascade_voted:**
1. Keep CGAR's deterministic resolver as the *backbone* — it already does 87.1%.
2. Wrap *every* LLM call site in XGrammar-style CFG-constrained decoding so Gemma-2 9B physically cannot emit malformed JSON or non-PyPI strings (whitelist constraint: package name must match `^[A-Za-z0-9_.\-]+$` AND appear in a prefetched PyPI index, blocking `sys`/`os` hallucinations at decode time).
3. Run agents only as *proposers* — Negotiator and BuildDoctor each emit a ranked top-k under self-consistency (3 samples, soft-vote per arXiv 2402.13212). The deterministic constraint solver still owns the decision.
4. Replace the LLM Critic with a Bandit-style deterministic validator (PyPI metadata + wheel filter + import-graph check). Critic becomes a *re-ranker*, not an overrider — the m4 failure mode is structurally impossible.
5. Reflexion memory scoped per-snippet only (drop session-wide bleed). Cross-snippet learning lives in the constraint store (HARD/SOFT) the way CGAR already does it — that's the *only* leaked state proven to help.

Target: 85%+ on smoke, threat to SMT-LLM novelty is preserved because (i) backbone is a discrete solver not Z3, (ii) the novelty is *grammar-constrained multi-agent proposers feeding a deterministic arbiter* — no published work does this for dep resolution.

## Papers with techniques DIRECTLY APPLICABLE

### Structured-output / agent reliability for small LLMs

**XGrammar — Flexible and Efficient Structured Generation Engine for LLMs** (arXiv 2411.15100, MLSys 2025; XGrammar-2 follow-up arXiv 2601.04426)
- What: Token-level CFG enforcement using a precomputed token mask cache; works with vLLM/SGLang. XGrammar-2 adds dynamic dispatch for agentic tool-calling specifically on small / compressed models.
- Solves problem 1: makes Gemma-2 9B's JSON output *provably* schema-valid — fixes "returns enum template verbatim" and wrong field types.
- Integration: wrap Ollama with vLLM or llama.cpp's GBNF grammar; emit one CFG per agent role.
- Novelty threat: **LOW** — pure decoding technique, no dep-resolution overlap.

**SLOT — Structuring the Output of Large Language Models** (arXiv 2505.04016)
- What: Post-processing layer + constrained decoding; Mistral-7B reaches 99.5% schema accuracy, beating Claude-3.5-Sonnet by 25pp.
- Solves problem 1: drop-in for the negotiation output and BuildDoctor diagnosis schemas.
- Integration: same as XGrammar; we can use SLOT's data-curation recipe to fine-tune a 1–3B post-processor if needed.
- Novelty threat: **LOW**.

**Small Language Models for Agentic Systems: A Survey** (arXiv 2510.03847)
- What: Survey of SLM-agent architectures, capabilities, deployment trade-offs.
- Solves problem 1/3: gives a citable taxonomy for our "small-LLM agent" framing.
- Integration: cite as the framing paper in the related-work section.
- Novelty threat: **LOW**.

### Hybrid rule + LLM and critic-as-verifier

**SecureFixAgent — Hybrid LLM Agent for Automated Code Repair** (arXiv 2509.16275)
- What: Bandit (deterministic static analyzer) + sub-8B LLM in detect–repair–validate loop; the LLM proposes patches, Bandit re-validates. Reports 87.83% accuracy with 8.11% FP on its task.
- Solves problems 2 + 4: rules detect and *validate*; LLM only proposes. Exactly the architecture our m4 should have used.
- Integration: structurally identical to wrapping CGAR's constraint solver around an LLM Negotiator that produces candidates only.
- Novelty threat: **MEDIUM** — same hybrid template, different SE task (security fixes vs dep resolution). Cite as the architectural ancestor; our novelty is the *constraint-graph-arbitrated* version.

**UniDebugger — Hierarchical Multi-Agent Framework for Code Repair** (EMNLP 2025, aclanthology 2025.emnlp-main.921)
- What: L1 local → L2 module → L3 global cascade; only escalates when previous level fails.
- Solves problem 5: confirms the cascade-on-confidence design we already use in MEMRES; gives us a recent peer-reviewed reference for the cascade thesis.
- Integration: cite as evidence that hierarchical cascade > flat blackboard for code repair. Reinforces our move *away* from m4's flat 5-agent blackboard.
- Novelty threat: **MEDIUM** — same cascade idea, different domain.

### Voting / self-consistency for small-model agents

**Soft Self-Consistency Improves Language Model Agents** (arXiv 2402.13212)
- What: For sequential agent tasks majority voting fails; soft scoring (continuous likelihood aggregation) recovers gains.
- Solves problem 4: lets Critic *rank* proposals without overriding — directly addresses our m4 Critic-override pathology.
- Integration: BuildDoctor and Negotiator each emit k samples, soft-vote into a score, deterministic solver picks the top-scoring *feasible* candidate.
- Novelty threat: **LOW**.

**Ranked Voting based Self-Consistency of LLMs** (arXiv 2505.10772)
- What: Ordinal preferential voting across multi-agent samples.
- Solves problem 4: alternative aggregation; complementary to soft self-consistency.
- Integration: secondary fallback if soft-voting ties.
- Novelty threat: **LOW**.

### Cascade / confidence routing

**GATEKEEPER — Improving Model Cascades Through Confidence Tuning** (arXiv 2502.19335)
- What: Tunable difficulty/quality threshold determines when to defer up the cascade.
- Solves problem 5: gives a principled tuning method for the cascade thresholds MEMRES picks heuristically.
- Integration: replace our hand-tuned cascade gates with GATEKEEPER's calibrated threshold.
- Novelty threat: **LOW**.

**CARGO — Confidence-Aware Routing of LLMs** (arXiv 2509.14899)
- What: Embedding regressor + binary classifier fallback for routing.
- Solves problem 5: routes snippets to "rule-only" vs "rule+LLM" track based on predicted difficulty — could cut our 70% no-LLM rate further.
- Integration: train the classifier on HG2.9K snippet features → predict CGAR-alone-suffices vs needs-LLM.
- Novelty threat: **LOW**.

### Distilled multi-agent into one small model

**MapCoder-Lite — Distilling Multi-Agent Coding into a Single Small LLM** (arXiv 2509.17489)
- What: 7B model with agent-wise LoRAs replays a multi-agent system; 13.2% → 28.3% on xCodeEval, 4× cheaper than 32B baseline.
- Solves problem 3 (and indirectly 1): eliminates inter-agent JSON serialization brittleness by collapsing the agents into one model with role switches.
- Integration: if m6 still hits JSON-serialization issues, distill into a single Gemma-2 9B with per-role LoRAs as a fallback architecture.
- Novelty threat: **MEDIUM** — same "small-LLM multi-agent" framing but for competitive-programming code-gen, not dep resolution.

### Reflexion contamination

**Meta-Policy Reflexion — Reusable Reflective Memory and Rule Admissibility** (arXiv 2509.03990)
- What: Adds rule-admissibility filters and reusable abstractions to Reflexion-style memory to prevent task-specific traces from contaminating new tasks.
- Solves "Reflexion contaminates current snippet" failure exactly. The fix is admissibility filtering, not abandoning Reflexion.
- Integration: filter our reflexion entries by admissibility (does this constraint typecheck against the *current* snippet's imports?) before retrieval.
- Novelty threat: **LOW**.

### Adjacent SE-agent benchmarks / related dep work (must cite, novelty risk)

**SMT-LLM — Breaking the Dependency Chaos (FSE'26)** (arXiv 2605.11772) — 83.6% HG2.9K with Z3 + selective LLM imputation. **HIGH threat**: same task, same benchmark. Our novelty must clearly differentiate from "SMT solver + LLM oracle" — m6's pitch is *grammar-constrained multi-agent proposers over a discrete constraint store* (no SMT, no temporal heuristic, no monolithic LLM).

**MEMRES (arXiv 2604.16941)** and **PLLM / Raiders of the Lost Dependency (arXiv 2501.16191)** — already in our table; cite as predecessors. No threat (ours).

**Survey of Benchmarks and Solutions in SE of LLM-Empowered Agentic Systems** (arXiv 2510.09721) — cite once in related-work scaffold.

## Recommended composed method — m6_constrained_cascade_voted

Single candidate (one is enough; m4/m5 failed because we built two competing things at once).

### File: `tools/cgar/src/m6_constrained_cascade_voted.py`

```
                 ┌─────────────────────────────────────────────┐
 Snippet ──────► │ Stage A: Deterministic Backbone (CGAR rules)│
                 │  - import extractor, py-version detector    │
                 │  - candidate graph builder (PyPI live)      │
                 │  - constraint solver (HARD/SOFT)            │
                 └────────┬────────────────────────────────────┘
                          │ unresolved? (confidence < τ from GATEKEEPER)
                          ▼
                 ┌─────────────────────────────────────────────┐
                 │ Stage B: LLM Proposer Pool (Gemma-2 9B)     │
                 │  All decoding gated by XGrammar CFG:        │
                 │  - PackageNegotiator → top-k pkg=ver        │
                 │     (CFG forces name ∈ PyPI prefetch index) │
                 │  - BuildDoctorAgent → typed constraint      │
                 │     (CFG forces enum: API_REMOVED|WHEEL|…) │
                 │  Each agent: 3 samples, soft self-consistency│
                 └────────┬────────────────────────────────────┘
                          │ ranked candidates + extracted constraints
                          ▼
                 ┌─────────────────────────────────────────────┐
                 │ Stage C: Deterministic Arbiter              │
                 │  - feed ranked candidates back to solver    │
                 │  - solver picks top-scoring FEASIBLE one    │
                 │  - LLM CANNOT override (architectural)      │
                 └────────┬────────────────────────────────────┘
                          │
                          ▼
                 ┌─────────────────────────────────────────────┐
                 │ Stage D: Docker Build → admissibility-filtered│
                 │  reflexion (per-snippet; cross-snippet only │
                 │  via HARD/SOFT constraint store)            │
                 └─────────────────────────────────────────────┘
```

### Agent I/O schemas (all CFG-enforced)

- **PackageNegotiator** in `{"imports": [str], "py_version": str, "denied": [pkg=ver]}` → out `{"candidates": [{"pkg": "<PyPI-whitelisted>", "ver": "<semver>", "rationale": str}]}` (k=5, sampled 3×)
- **BuildDoctorAgent** in `{"docker_log_tail": str, "attempted": pkg=ver}` → out `{"culprit_pkg": "<whitelisted>", "error_class": "API_REMOVED|WHEEL_MISSING|VERSION_FLOOR|PY_VERSION|OTHER", "evidence_span": [int,int]}`
- **No Critic agent.** Verification = constraint solver + Docker exit code. Period.

### Where rules sit (the deterministic backbone, owns all decisions)

- Import → package mapper (ErrorPatternKB)
- Py-version detector (rule-locked, no LLM override — m5's one good lesson)
- Constraint solver with HARD/SOFT store + wheel-availability filter
- PyPI prefetch index (~50k popular names) used as the CFG terminal alphabet for package names → kills stdlib hallucination at decode time

### Where LLM agents sit (augmentation only)

- Only invoked when solver returns `UNRESOLVED` or `CONFIDENCE<τ`
- Only produce ranked proposals / typed observations
- Output is always a *constraint* the solver can typecheck, never a decision

### Why this should hit 85%+ on Gemma-2 9B

1. CGAR-rule alone is at 87.1% on HG2.9K → we're protecting a floor, not chasing a ceiling.
2. The new LLM calls only fire on the residual ~13% (ImportError-dominated per CLAUDE.md) where rules are uncertain — exactly the cases where MEMRES's LLM helped.
3. XGrammar/SLOT close the JSON-failure gap that killed m4/m5 — no malformed structures, no stdlib hallucination, no enum-template echoing.
4. Soft self-consistency with the LLM as ranker (not decider) makes Critic-overrides architecturally impossible.
5. Per-snippet Reflexion scope removes the cross-snippet contamination we observed.

### Threats to plan / honest risks

- Ollama doesn't natively expose token-level CFG masking. Migration to vLLM or llama.cpp+GBNF is required → infra cost ~1–2 days.
- Prefetching 50k PyPI names into a CFG terminal alphabet is large; XGrammar's mask cache handles this but verify on Gemma-2 9B specifically.
- If LLM proposers add <2pp over rule-only, the multi-agent story is empirically thin — be ready to honestly report that and pivot the contribution toward "constrained-decoding makes small-LLM dep-resolution agents actually work" (still a contribution; still G1-compliant).

## Sources

- XGrammar — https://arxiv.org/abs/2411.15100
- XGrammar-2 — https://arxiv.org/abs/2601.04426
- SLOT — https://arxiv.org/abs/2505.04016
- Small LMs for Agentic Systems (Survey) — https://arxiv.org/abs/2510.03847
- SecureFixAgent — https://arxiv.org/abs/2509.16275
- UniDebugger — https://aclanthology.org/2025.emnlp-main.921.pdf
- MapCoder-Lite — https://arxiv.org/abs/2509.17489
- Soft Self-Consistency — https://arxiv.org/abs/2402.13212
- Ranked Voting Self-Consistency — https://arxiv.org/abs/2505.10772
- GATEKEEPER — https://arxiv.org/abs/2502.19335
- CARGO — https://arxiv.org/abs/2509.14899
- Meta-Policy Reflexion — https://arxiv.org/abs/2509.03990
- SMT-LLM (FSE'26, novelty-threat reference) — https://arxiv.org/abs/2605.11772
- MEMRES — https://arxiv.org/abs/2604.16941
- PLLM / Raiders — https://arxiv.org/abs/2501.16191
- Agentic SE Benchmarks Survey — https://arxiv.org/abs/2510.09721
- Reflexion (original) — https://arxiv.org/abs/2303.11366

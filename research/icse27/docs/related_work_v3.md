# Focused Lit Review v3 — Conflict Dependency Resolution

Round 3. Prior sweeps (`related_work.md` 30 papers, `related_work_v2.md` 17 papers) covered general agentic SE + small-LLM reliability. This sweep is FOCUSED: where does *dependency conflict resolution* as a subfield have unclaimed contribution space, given CGAR is already at 87.1% / 83.2% and all 4 multi-agent LLM designs (m4–m7) failed to lift above 84%?

Honest bottom line up front: **the agent thesis is in trouble.** The empirical evidence says (a) CGAR's deterministic backbone already does the work, (b) the remaining 13% is dominated by *structurally impossible* cases (Py2 wheels, proprietary modules, removed APIs), and (c) Gemma-2 9B cannot reliably add value on top. Strong contributions from this corner are *not* "yet another agent design." The unclaimed space is in characterizing/exploiting the structure of the residual.

---

## TL;DR — Where is the unclaimed contribution space?

- **Gap 1 — No published *quantitative taxonomy* of irreducible dependency conflicts.** PyConf (ICSE'24) [arXiv 2310.12598] taxonomizes 15 *configuration* issue kinds. Watchman/Yu (ICSE'20) [yepangliu.github.io] taxonomizes 235 *historical* conflict issues by manifestation pattern. Neither characterizes the **modern lower bound**: snippets that *no resolver can fix today* and *why*. Our CLAUDE.md already has the 41.6/25.8/13.3/8.1/4.0% breakdown across 310 snippets — that *is* a taxonomy, and it is publishable.
- **Gap 2 — No work formally connects "constraint solver + LLM oracle" to dynamic execution evidence.** TraceFixer (arXiv 2304.12743) and TraceRepair (arXiv 2604.02647) repair bugs from execution traces but ignore deps. Our Docker build error → FailureInjector → typed constraint pipeline is exactly this, but no paper has framed it as **"runtime-grounded constraint refinement for dep resolution."** The ICSE A* novelty handle is here, *if* we frame it as a contribution and ablate it properly.
- **Gap 3 — No work has explicitly used a *time-travel package index* (PyPI snapshot at a temporal cutoff) as a *constraint primitive* for dep resolution.** pypi-timemachine is an *operational tool*, never a research instrument. For snippets that "API was removed" or "wheel ABI floor moved," a snapshot is a free oracle. This is also a paper-worthy framing nobody has claimed.
- **Gap 4 — Cross-ecosystem dep-resolution techniques are not ported to Python.** PubGrub (Dart/Bundler/Poetry/uv) uses CDCL with learned incompatibilities. Cargo allows multi-version coexistence in the resolution. Go uses minimum-version selection. Nobody has empirically tested whether porting *learned-incompatibility CDCL* to Python's LLM-augmented dep stack helps. CGAR's `HARD/SOFT` store is *informally* exactly this; formalizing it as CDCL is a contribution handle.
- **Best fit for ICSE A* given our constraints:** Reframe the paper around **"the irreducible-floor characterization + a runtime-grounded CDCL constraint store, with the agent as a *bounded* proposer for the empirically-soluble residual."** Multi-agent thesis preserved (locked by user). Small LLM viable (we don't need it to be smart, we need it to be a typed proposer for a CDCL-style learning solver). Beats CGAR 87% because the formalized CDCL + snapshot oracle catches the API-removed cases CGAR currently leaves on the table. See "Recommended path" below.

---

## Conflict resolution as a research subfield

### Theoretical foundations
- **Version selection is NP-complete** even for the basic SAT-style encoding [Mancinelli et al. via "Dependency Solving Is Still Hard, but We Are Getting Better at It", Abate et al., arXiv 2011.07851]. This is the citable foundation our paper has been missing — every prior round skipped the complexity foundation.
- **CDCL (conflict-driven clause learning) > naive backtracking** for large dep graphs [PubGrub, Weizenbaum 2018; production implementation in `uv`, Poetry, Bundler]. PubGrub's central insight — record *learned incompatibilities* to prune future search — is functionally what CGAR's `constraint_store.py` does informally with HARD/SOFT.
- **Diamond dependency** is the irreducible hardness driver [research.swtch.com/version-sat]. Where two packages need incompatible versions of a shared transitive dep, no solver can fix it. This is the structural reason for part of our 10.7% floor.

### Recent surveys / empirical studies (2024-2026) — actually cite-able
- **"Less is More? An Empirical Study on Configuration Issues in Python PyPI Ecosystem"** (ICSE 2024) [arXiv 2310.12598]. Identifies **15 kinds** of configuration issues across 183,864 library releases; **68%** are detectable only via source-level checks. Releases their `PyConf` detector + `VLibs` benchmark. **Most important citation we are missing.** They report PyEGo infers deps for only **65%** of library releases — confirms the 45% number we see is on different (harder) data, not a refutation. **Cite as: the empirical taxonomy our floor analysis extends.**
- **ModuleGuard** (ICSE 2024) [arXiv 2401.02090]. Detects *module conflicts* — distinct package names sharing import names. Our `ErrorPatternKB` + `module_mapper` does this informally. **Cite for: prior work on the module-naming ambiguity that drives part of CGAR's ImportError residual.**
- **Watchman** (ICSE 2020) [yepangliu.github.io files paper ICSE2020]. Original empirical study of 235 DC issues across 124 Python projects. **89.8%** are remote-dep conflicts; **1/4 each** caused by "too-specific constraint" / "upper-bound tipped." Foundational; cite for problem motivation.
- **PyPitfall** (2025) [arXiv 2507.18075]. 4,655 packages *require* known-vulnerable versions; 141,044 *permit* vulnerable ranges (of 378,573 PyPI packages). **Cite for: supply-chain framing if we want a supply-chain angle.**
- **"How Deep Does Your Dependency Tree Go? An Empirical Study of Dependency Amplification Across 10 Package Ecosystems"** (2025) [arXiv 2512.14739]. Cross-ecosystem comparison. Confirms Python's amplification depth is among the highest. **Cite as: ecosystem-comparative motivation.**
- **PCART** (2024) [arXiv 2406.03839]. Automated repair of **Python API parameter compatibility issues**. 96.49% F1 on detection, 91.36% repair on 47,478 test cases / 33 libs. **Cite as: complementary repair layer — we resolve which version to use, PCART rewrites the call site once version is chosen.** This is also a potential *integration*: CGAR picks the older version, PCART rewrites the deprecated API call. ICSE A* novelty: "two-layer repair — dep version + API call." Worth considering.

### Cross-ecosystem techniques worth porting
- **CDCL with persistent learned incompatibilities** (PubGrub). Maps 1:1 onto `constraint_store.py`. Formalize it.
- **Minimum-version selection** (Go modules). For our irreducible-floor cases, *intentionally* pick the *oldest* version with a wheel is sometimes the only solution. Our solver implicitly does this via `add_upper_bound`; formalize as a MVS variant.
- **Multi-version coexistence in one resolution** (Cargo). Python's flat `site-packages` makes this hard, but `uv`'s `--isolated` and virtualenv-per-snippet approach already does it. CGAR effectively does this per-snippet. Cite as architectural inspiration.

### Recent surveys we should cite for framing only
- "Dependency Solving Is Still Hard, but We Are Getting Better at It" (Abate et al., 2020) [arXiv 2011.07851] — the foundational survey.

---

## Approaches beyond our current arsenal

For each: 1-line description, why we didn't try it, whether it's worth trying now.

### 1. Execution-trace-grounded constraint refinement
- *What:* Instrument the Docker build/run, extract trace events (import order, attribute access, missing-attribute traces), feed back as typed constraints. TraceFixer (arXiv 2304.12743) and TraceRepair (arXiv 2604.02647) do this for general APR.
- *Why we didn't try:* CGAR's `failure_injector.py` already does a *log-tail* version of this; we never extended to instrumented traces.
- *Worth trying now?* **Yes, high-leverage.** Many residual ImportError cases are "import X works, but `X.foo` fails at runtime" — solvable only with trace evidence. **This is the m6-extension that would lift past 87%.**

### 2. Time-travel PyPI snapshot as a constraint oracle
- *What:* For "API was removed" failures, query PyPI as-of date D and constrain `release_date(pkg, ver) < D`. pypi-timemachine exposes this via PEP-503.
- *Why we didn't try:* Wasn't on the radar; CGAR's `add_upper_bound` does it implicitly via *version* not *date*.
- *Worth trying now?* **Yes — small effort, novel framing.** Many of our HG2.9K snippets are from gist timestamps; we have a free `D` per snippet. Adding a date-based constraint primitive is ~50 LOC and gives the paper a clean "temporal constraint" angle.

### 3. Mining GitHub for known-working configurations
- *What:* Mine successful CI runs / lockfiles to seed the constraint store with proven configurations. The Knowledge Oracle already does a version of this from PLLM historicals.
- *Why we didn't try:* We did, via `knowledge_oracle.py` and `cooccurrence_miner.py`.
- *Worth trying now?* Already in arsenal; could scale up corpus, but diminishing returns.

### 4. Type-driven inference for Python pkgs (Hindley-Milner analog)
- *What:* Use type signatures (from PyTorch's `Tensor`, NumPy's `ndarray`, etc.) to constrain compatible versions.
- *Why we didn't try:* Python's gradual typing makes this very weak signal.
- *Worth trying now?* **No.** Search returned only general HM tutorials — no SE applications to dep resolution. Type inference is too weak for version constraints; this is a dead end.

### 5. Knowledge-graph approach (post-PyEGo)
- *What:* Build a KG of pkg–pkg–version edges; do graph reasoning for compatibility. PyEGo / PyCRE both do this [ICSE'22].
- *Why we didn't try:* PyEGo is a baseline already at 45.0% on HG2.9K — empirically dominated by CGAR.
- *Worth trying now?* **No new directions found.** ICSE 2025 has "PackHunter" for C/C++ but nothing newer for Python dep KGs. Saturated.

### 6. Proactive conflict prediction (ML classifier predicts conflict before build)
- *What:* Classifier predicts "this requirements.txt will conflict" without actually building. The 2508.05034 paper does something similar for OpenStack change deps.
- *Why we didn't try:* Out of scope; we receive snippets, not patches to predict.
- *Worth trying now?* **No.** Wrong problem framing for our task (we *fix*, not *predict*).

### 7. Self-healing CI agents (autonomous Docker repair)
- *What:* VIGIL (arXiv 2512.07094), self-healing agent runtimes; Android build repair (arXiv 2510.08640).
- *Why we didn't try:* The agents are over-LLM'd for our deterministic-floor problem.
- *Worth trying now?* **No directly**, but the "domain-specific tools for LLM agents" pattern from 2510.08640 is what CGAR already does. Cite as architectural precedent.

### 8. Software-supply-chain framing
- *What:* Frame resolution as also picking *non-vulnerable* versions. PyPitfall, propagation-based vulnerability (arXiv 2506.01342).
- *Why we didn't try:* Out of scope.
- *Worth trying now?* **Maybe as a secondary contribution** — adding a "vuln-aware constraint" to the solver (3rd column in `constraint_store`) is cheap and gives an additional metric (% solutions vuln-free) that no competitor reports. *But* it dilutes the dep-resolution focus. Probably defer.

### 9. Reproducible-build research
- *What:* Reproducibility study (ICSE'25): PyPI achieves only **12.2%** reproducible builds [Nesbitt 2025; cmu.edu icse25_rb.pdf].
- *Why we didn't try:* Different problem (bit-identical builds, not "any build that runs").
- *Worth trying now?* **No.** Different problem; cite only as ecosystem-context.

---

## The "irreducible floor" — is this itself a contribution?

### Published characterizations
Searched explicitly. Nothing matches.

- Watchman (ICSE'20) classifies historical *issues* by root cause but does **not** stratify by "fixable today vs not."
- PyConf (ICSE'24) catalogs *configuration* issue kinds but the question is "does the lib release work standalone?", not "can any resolver fix this snippet today?"
- "Dependency Solving Is Still Hard" (Abate 2020) argues hardness in the SAT sense, not empirical fraction-unfixable.
- Pip's docs enumerate error messages, not formal categories.

### Gap analysis — is there a paper-worthy taxonomy nobody has published?

**Yes, and we already have the data.** Our 310-snippet irreducible-floor breakdown (CLAUDE.md):
- 41.6% Py2 syntax / no Py2 wheels on modern manylinux
- 25.8% ImportError on system/private/proprietary packages
- 13.3% pkg absent from PyPI entirely
- 8.1% native build failure (glibc / ABI)
- 4.0% API removed with no compatible wheel for any older ver

This is a 5-class taxonomy on **2,891 snippets with ground-truth pass/fail labels** from the strongest extant resolver (CGAR itself). **Nobody has published anything analogous for Python.** PyConf studied PyPI library releases (not failing snippets); Watchman studied historical issues (not modern resolver residuals).

**Contribution framing:** "An Empirical Lower Bound for Automated Python Dependency Resolution: 10.7% Are Irreducible, And Here's Why." Even if our agent contribution is weak, this empirical floor characterization alone is a strong ICSE A* contribution — it gives the community a target ("don't bother chasing the last 10.7% with smarter resolvers; instead build wheel fallback for Py2, mark proprietary packages explicitly, fix the long-tail wheel-build issue").

**Honest caveat:** This is an *empirical* paper, not an *agent* paper. It conflicts with the user-locked multi-agent thesis. We can include it as **Contribution 3** of the agent paper (alongside the method + the constraint-store formalization), but it cannot be the sole pitch.

---

## Reframing options for ICSE A*

Given empirical evidence (CGAR 87.1%, multi-agent doesn't lift), TRULY NOVEL angles:

### Option 1 — "Runtime-Grounded CDCL for Dependency Resolution" (RECOMMENDED, strongest novelty/feasibility)
- *Thesis:* CGAR's `constraint_store` is informally a CDCL solver with learned incompatibilities. Formalize it as CDCL, add **execution-trace-grounded constraint extraction** (not just log-tail regex — instrument Docker builds for richer signals), and use **bounded LLM agents as typed proposers** (XGrammar / SLOT from v2) for the residual where CDCL is stuck.
- *Novel against existing work:* PubGrub is offline CDCL (no LLM, no runtime). SMT-LLM (arXiv 2605.11772) uses Z3 with LLM imputation but on a *flat* SMT encoding, not CDCL with runtime feedback. No published work does runtime-grounded CDCL.
- *Multi-agent role:* `TraceInspector` agent (instrumented import/attribute traces), `ConstraintLibrarian` agent (CDCL clause learning), `Negotiator` agent (typed proposer over PyPI alphabet). All grammar-constrained per v2.
- *Beats CGAR 87% empirically:* Yes, *if* we add the trace-grounded constraint primitives — they catch the "X imports OK, X.foo fails" cases that CGAR misses.
- *Honest risk:* If trace-grounding gives only +1pp, the contribution is the formalization+ablation, not the lift. Still publishable but weaker.

### Option 2 — "An Empirical Lower Bound for Automated Python Dependency Resolution" (PURE EMPIRICAL)
- *Thesis:* Characterize the irreducible 10.7% empirically across HG2.9K, GitChameleon, and a third benchmark (PyConf's `VLibs`). Stratify by Py2/Wheel/Proprietary/Removed/NoPyPI. Estimate ecosystem-wide unfixable fraction.
- *Novel against existing work:* PyConf is the closest; we extend by adding resolver-failure stratification.
- *Multi-agent role:* None (would have to invent one; honest paper says "agents don't help here").
- *Conflict with user lock:* **High.** This is not a multi-agent paper.
- *Probability of A*:* High *as a pure empirical paper*. Low *as the agent paper* the user wants.

### Option 3 — "Temporal Dependency Resolution: Snapshot Oracles for API-Drift Failures"
- *Thesis:* Frame "API was removed" failures as a temporal-constraint problem. For each snippet with a timestamp T (gist creation date), constrain solver to `release_date(pkg, ver) ≤ T + ε`. Use pypi-timemachine as a PEP-503 snapshot index. Show this catches K% of currently-irreducible "API removed" failures.
- *Novel against existing work:* Nobody has used PyPI temporal snapshots as a constraint primitive. pypi-timemachine exists as a tool, not a research instrument.
- *Multi-agent role:* `TemporalArchaeologist` agent extracts T from snippet/gist metadata (LLM judgment call — matches Rule 5).
- *Beats CGAR 87%:* On the API-Removed subset (4.0% of 10.7% floor = ~12 snippets), yes. On full HG2.9K, +0.4pp at most. Weak.
- *Honest assessment:* Cute angle, too narrow to carry a paper.

### Option 4 — Two-layer repair (dep version + API call rewriting via PCART)
- *Thesis:* Resolve dep version (CGAR backbone), then rewrite deprecated API calls (PCART-style). Cover both axes of "API drift."
- *Novel against existing work:* PCART rewrites calls assuming version is fixed; CGAR fixes version assuming call is fixed. Doing both jointly is unclaimed.
- *Multi-agent role:* `VersionNegotiator` + `APIRewriter` agents.
- *Beats CGAR 87%:* On GitChameleon (which is *designed* around API drift), yes — probably +5–10pp. On HG2.9K, modest +1–2pp.
- *Honest risk:* PCART is closed-source; we'd reimplement. Increases scope.

---

## Recommended path (1-2 candidates, evidence-grounded)

### Primary recommendation: **Option 1 + empirical floor characterization from Option 2 as Contribution 3**

Concrete method outline:

```
Paper title (draft): "Runtime-Grounded CDCL with Bounded LLM Agents for
                      Python Dependency Resolution"

Contribution 1 (method): Formalize CGAR's constraint store as CDCL with
  learned incompatibilities (porting PubGrub's clause-learning to Python
  dep resolution). Add execution-trace-grounded constraint extraction
  (instrumented Docker builds, not just log regex).

Contribution 2 (method): Bounded LLM agents as XGrammar-constrained typed
  proposers (m6 architecture from v2) — agents propose CDCL clauses, never
  decide. Soft-self-consistency over k samples per agent.

Contribution 3 (empirical): The first published characterization of the
  irreducible floor (10.7%) across HG2.9K + GitChameleon + VLibs, stratified
  by 5 root-cause classes. Establishes the upper bound for any resolver-only
  approach.

Ablations (mandatory per G5):
  - CGAR-rule alone (87.1% baseline)
  - CGAR-rule + CDCL formalization (no LLM, no traces)
  - + trace-grounded constraints (no LLM)
  - + LLM proposers (full system)
  - w/o each agent role
  - w/o XGrammar constraint
  - w/o soft self-consistency

Statistical: 3 seeds × HG2.9K + GitChameleon + VLibs. Wilcoxon paired.
Bootstrap 95% CI on headline. Per G6.
```

#### Why this fits the constraints:
- **Multi-agent thesis (user lock):** YES — TraceInspector + ConstraintLibrarian + Negotiator + (optional) Critic-as-reranker. m6 architecture preserved.
- **Small LLM viable:** YES — Gemma-2 9B as XGrammar-constrained proposer, never decider. Per v2's diagnosis.
- **Beats CGAR 87%:** Plausibly yes via trace-grounding. If only +1–2pp, the contribution shifts to formalization + Contribution 3 (empirical floor) — still A* defensible.
- **ICSE A* novelty defensible:**
  - vs SMT-LLM (arXiv 2605.11772): we use CDCL not flat SMT; we add runtime traces; we use grammar-constrained agents. All three differ.
  - vs MEMRES/PLLM: we add CDCL formalization + runtime grounding + empirical floor characterization.
  - vs PubGrub: PubGrub is offline; ours is runtime-grounded with LLM proposers.
  - vs PyEGo/ReadPyE: those are KG-based; ours is constraint-CDCL-based.
  - vs PyConf (ICSE'24): PyConf catalogs *library configuration* bugs; we catalog *resolver failure* causes — strictly different unit of analysis.

### Secondary recommendation (lower risk, lower ceiling): **Option 2 alone, pure empirical paper**

If by the next sprint the agent variants still don't lift, **defect** to Option 2 as a pure empirical / measurement paper. ICSE accepts empirical-only papers. PyConf at ICSE'24 is a precedent. Pitch:

- "An Empirical Lower Bound for Automated Python Dependency Resolution"
- Numbers we already have: CGAR 87.1% / 83.2% across two benchmarks, 5-class floor taxonomy on 310 snippets, all 4 LLM agent designs failing to lift.
- Adds: VLibs benchmark from PyConf for third dataset, reproduction of PyEGo/ReadPyE/PLLM as baselines (we have all numbers).
- Honest contribution: "Multi-agent LLMs do not currently lift Python dep resolution above the deterministic CDCL floor — here's why, with 5 ablated agent architectures."

This is a **negative-result-as-contribution** paper in the ICSE empirical track. ICSE has accepted such papers (e.g., "Less is More?" is partially a negative result about PyEGo).

---

## Sources

- "Dependency Solving Is Still Hard, but We Are Getting Better at It" (Abate et al., 2020) — https://arxiv.org/abs/2011.07851
- PyConf / "Less is More? An Empirical Study on Configuration Issues in Python PyPI Ecosystem" (ICSE 2024) — https://arxiv.org/abs/2310.12598
- ModuleGuard (ICSE 2024) — https://arxiv.org/abs/2401.02090
- Watchman (ICSE 2020) — https://yepangliu.github.io/files/ICSE2020_Watchman.pdf
- PyPitfall (2025) — https://arxiv.org/abs/2507.18075
- "How Deep Does Your Dependency Tree Go? Dependency Amplification Across 10 Ecosystems" (2025) — https://arxiv.org/abs/2512.14739
- PCART — Automated Repair of Python API Parameter Compatibility (2024) — https://arxiv.org/abs/2406.03839
- APIScanner (deprecated API detection) — https://arxiv.org/abs/2102.09251
- TraceFixer (execution-trace-driven repair) — https://arxiv.org/abs/2304.12743
- TraceRepair (runtime-traces + multi-agent debate) — https://arxiv.org/abs/2604.02647
- Blended Analysis for Predictive Execution (FSE 2025) — https://dl.acm.org/doi/10.1145/3729402
- DynaPyt (Python dynamic analysis framework) — https://dl.acm.org/doi/pdf/10.1145/3540250.3549126
- VIGIL (self-healing LLM agent runtime) — https://arxiv.org/abs/2512.07094
- Android Build Repair via LLM Agents + Domain Tools — https://arxiv.org/abs/2510.08640
- Propagation-Based Vulnerability Impact Assessment (Supply chains) — https://arxiv.org/abs/2506.01342
- ML for Software Change Dependency Prediction (OpenStack) — https://arxiv.org/abs/2508.05034
- pypi-timemachine (operational tool, not paper) — https://github.com/astrofrog/pypi-timemachine
- "Version SAT" (Russ Cox, complexity foundations) — https://research.swtch.com/version-sat
- PubGrub (CDCL-based version solving) — https://nex3.medium.com/pubgrub-next-generation-version-solving-2fb6470504f
- An Empirical Study on Reproducible Packaging in Open-Source Ecosystems (ICSE 2025) — http://www.cs.cmu.edu/~ckaestne/pdf/icse25_rb.pdf
- DockerMock (pre-build Dockerfile fault detection) — https://arxiv.org/abs/2104.05490
- Dockerfile Flakiness: Characterization and Repair — https://arxiv.org/abs/2408.05379
- smartPip (ASE 2022, SMT-based dep resolution) — https://dl.acm.org/doi/10.1145/3551349.3560437
- PyCRE / Conflict-aware Inference with Domain Knowledge Graph (ICSE 2022) — https://arxiv.org/abs/2201.07029
- Previously cited (carryover):
  - SMT-LLM "Breaking the Dependency Chaos" — https://arxiv.org/abs/2605.11772
  - MEMRES — https://arxiv.org/abs/2604.16941
  - PLLM / "Raiders of the Lost Dependency" — https://arxiv.org/abs/2501.16191
  - GitChameleon 2.0 — https://arxiv.org/abs/2507.12367

# Novelty Matrix — m8 vs m9 vs Existing Literature

Cross-checked against `related_work.md` (30 papers), `related_work_v2.md`
(17 papers), `related_work_v3.md` (27 papers). Goal: confirm both
candidate proposed methods (m8, m9) have **claimable novelty** that
does not duplicate prior work. Per Rule 5 + G1 + G2 in CLAUDE.md.

If a row says "✓ NOVEL" we have a defensible distinguisher.
If a row says "⚠ RISK" we need to be more careful in the paper framing.
If a row says "✗ DUPLICATE" we should NOT claim it as contribution.

## m8 — Runtime-Grounded CDCL

| Contribution | Most-similar prior work | How m8 differs | Verdict |
|---|---|---|---|
| **C1** Formalize HARD/SOFT/UPPER store as CDCL with combo clause learning | PubGrub (Dart/Cargo/uv 2018+) — CDCL for offline dep resolution | PubGrub is offline; m8 is **runtime-augmented + LLM-proposer-feeding**. PubGrub doesn't have an LLM in the loop, doesn't use Docker execution as feedback. | ✓ NOVEL |
| | SMT-LLM (Chowdhury, FSE'26, arXiv 2605.11772) — Z3 + selective LLM imputation | They use **flat SMT** (At-Most-One, At-Least-One, implications). m8 uses **CDCL with combo clause learning** (PubGrub-style 2-literal forbidden combos). Different solver paradigm. | ✓ NOVEL |
| | CGAR (ours, FSE'26) — informal HARD/SOFT store | CGAR already uses HARD/SOFT, but **never formalized** as CDCL, never learns **combo clauses** (only unit clauses), never published the algorithm. m8 makes it formal + adds clause learning. | ✓ NOVEL (formalization is the contribution) |
| **C2** Runtime-grounded constraint extraction via injected import/attribute tracer | TraceFixer (arXiv 2304.12743) — execution-trace driven APR | TraceFixer repairs **general bugs**, not deps. Doesn't extract typed constraints. Doesn't feed a constraint solver. | ✓ NOVEL |
| | TraceRepair (arXiv 2604.02647) — multi-agent debate over runtime traces | Same — APR not deps. No constraint-emission interface. | ✓ NOVEL |
| | CGAR's `failure_injector.py` — regex over Docker log tail | m8 **instruments the snippet** with import/excepthook hooks → structured markers from inside container → ORDERS of magnitude richer signal than log-tail regex. | ✓ NOVEL |
| **C3** 5-class empirical floor taxonomy on 248 irreducible HG2.9K snippets | PyConf (ICSE'24, arXiv 2310.12598) — 15-class configuration-issue taxonomy on library releases | PyConf studies **library releases** (does the lib work?). m8 studies **resolver failures** (do current resolvers fail?). Different unit of analysis. | ✓ NOVEL |
| | Watchman (ICSE'20) — 235 historical conflict issues | Watchman is **historical** issue mining. m8 is **modern resolver residual** characterization. | ✓ NOVEL |
| | (none found that quantifies the irreducible floor for Python dep resolution) | Searched explicitly in v3. No match. | ✓ NOVEL (first-of-kind empirical) |

**m8 overall verdict:** All three contributions defensible. C3 is the
*safest* (purely empirical, reproducible script). C1 is the *most
theoretically interesting* (CDCL formalization). C2 is the *highest-risk*
because if the trace-grounded layer adds <2pp lift, the empirical
support is thin (mitigation: ablate against m7 to isolate the trace
mechanism's contribution).

## m9 — Temporal Snapshot Oracle

| Contribution | Most-similar prior work | How m9 differs | Verdict |
|---|---|---|---|
| **C1** (shared with m8) CDCL formalization | (same as m8) | (same as m8) | ✓ NOVEL |
| **C2'** Temporal authorship-era constraint as a first-class blackboard artifact | SMT-LLM's "two-pass era-biased selection" (Chowdhury FSE'26) — uses median PyPI upload time as **post-hoc re-ranker** | m9 uses temporal estimate as **upfront constraint** consumed by the solver, not a re-ranker. LLM TemporalArchaeologist reads snippet+imports+comments to infer year (vs SMT-LLM's heuristic median). | ⚠ RISK (medium-similar; framing must be precise) |
| | pypi-timemachine (open-source tool, not paper) | Tool exposes snapshot endpoint but no paper has used it as a research instrument or constraint primitive. | ✓ NOVEL |
| | "When LLMs Lag Behind — Evolving APIs Knowledge Conflicts" (arXiv 2604.09515) — characterizes API evolution gaps | They DOCUMENT the problem; m9 SOLVES a subset of it using temporal constraints. | ✓ NOVEL |
| **C3** (shared with m8) Empirical floor taxonomy | (same as m8) | (same as m8) | ✓ NOVEL |

**m9 overall verdict:** Defensible but **C2' has elevated similarity to
SMT-LLM**. The novelty is in the *blackboard-first-class constraint*
framing vs SMT-LLM's *post-hoc re-ranking*. The paper must be precise:
"SMT-LLM uses median timestamp as a selection heuristic; m9 uses LLM-
inferred year as a hard constraint that prunes the candidate set BEFORE
the solver runs." This is a real algorithmic difference but reviewers
will need to be convinced.

**Honest risk surfaced (per G8):** If C2' empirical lift is <2pp, the
contribution collapses to "we tried temporal constraints, they didn't
add value beyond SMT-LLM's heuristic" — a negative result. Acceptable
in the paper as an ablation row but cannot be the headline.

## Combined-method analysis: m8 ∪ m9 (potential m11)

If both m8 (runtime traces) and m9 (temporal) add value independently,
combining them is straightforward (both use the same CGAR-gate Stage A;
m8 adds Stage B trace-grounded clauses, m9 adds Stage B' temporal
filter). Should one win and the other lose, the paper claims the
winning mechanism only. We do NOT pre-build m11 — it's not novel unless
both ablations are positive.

## What we explicitly do NOT claim (G1 compliance)

To avoid reviewer pushback for over-claiming:

- **NOT a SAT/SMT-solver paper.** m8's CDCL formalism is a *characterization*
  of CGAR's existing store + a *small extension* (combo clauses), not a
  new SAT/SMT algorithm. We cite PubGrub/SMT-LLM and clearly defer to
  them on solver design.
- **NOT a "multi-agent debate" paper.** Empirically (m4 evidence)
  debate caused harm with small LLMs. We use bounded *typed proposers*,
  not debaters. The architecture is more "blackboard + constraint solver"
  than "agents arguing." Multi-agent thesis is preserved (3 specialized
  agents) but reviewers see it framed as "bounded proposers."
- **NOT a "new benchmark" paper.** We use HG2.9K + GitChameleon + (planned)
  VLibs from PyConf. The benchmark contribution is the irreducible-floor
  characterization, not a new dataset.
- **NOT a "scaling laws for agentic SE" paper.** We tested only Gemma-2 9B.
  Conclusions about "small LLM agent reliability" must be framed as
  Gemma-2 9B-specific, not generalized.

## Outstanding novelty concerns to monitor during runs

1. If m9 wins, **frame as "upfront temporal pruning vs SMT-LLM's median-rerank heuristic"** — emphasis on *blackboard-first-class* and *upfront* vs *post-hoc*. Need 1-2 concrete worked examples in paper showing the difference catches cases SMT-LLM's median heuristic misses.
2. If m8 wins, **frame as "instrumented runtime trace vs log-tail regex"** — emphasis on *structured markers* vs *unstructured log parsing*. Need a trajectory comparison example: snippet X → log-tail tells us little vs trace tells us exact module + attr.
3. If both add ≤2pp, **the lift is too small for either as headline**. Fall back to C1 (CDCL formalization) + C3 (floor taxonomy) as the contribution backbone, treat m8/m9 mechanisms as "modest auxiliary lift" rather than headline novelty.

## Tracker source

- `related_work.md` (round 1)
- `related_work_v2.md` (round 2 — small-LLM agent reliability)
- `related_work_v3.md` (round 3 — conflict dep resolution subfield)
- `floor_taxonomy.md` (C3 empirical data, reproducible)
- This file = the explicit novelty cross-check before launching expensive runs.

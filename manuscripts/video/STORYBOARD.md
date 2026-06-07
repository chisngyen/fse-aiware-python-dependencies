# Storyboard — MEMRES & CGAR presentation video

**Duration:** ~15–18 min · **Aspect:** 16:9 1920×1080 · **FPS:** 60
**Pipeline:** Pure Manim (no Blender). Black 3blue1brown-style background. Vietnamese narration, English technical terms.
**Palette:** `BG #0E1518` (near-black), `ACCENT #EB811B` (warm orange), `TEAL #4FB3BF`, `PURPLE #9B7EDE`, `SUCCESS #5CD68A`, `ALERT #FF6B6B`, `INK #ECEFF1`.

The video maps **1-to-1 with `../slide/main.tex`** (23 main slides, with Related Work split across 2 scenes → 24 scenes total). Narrative arc: **Problem → MEMRES → CGAR → Results → Limits → Future**.

---

## Master timeline

| # | Slide / topic | Scene class | Approx | Animation highlights |
|---|---|---|---|---|
| 1  | Title                                 | `Title`                  | 25 s | Starfield converges → two-tone "MEMRES & CGAR" → gradient underline |
| 2  | Nội dung chính (Outline)              | `Outline`                | 15 s | 4 numbered tiles stagger-fade |
| 3  | Bối cảnh (Context)                    | `Context`                | 40 s | Old code panel → red glitch overlay → "Environment is dead" |
| 4  | Bài toán & Yêu cầu đánh giá           | `ProblemIO`              | 50 s | INPUT code → ? → OUTPUT pinned env + budget badges |
| 5  | The Dependency Gap                    | `DependencyDomino`       | 55 s | Each problematic `import` **morphs** into a constraint card; chain knocks over |
| 6  | Bùng nổ tổ hợp                        | `CombinatorialExplosion` | 35 s | 500K count-up; ∏\|D_i\| formula reveal |
| 7  | Datasets                              | `Datasets`               | 25 s | Two stat columns (2,891 HG2.9K / 328 GitCh) count-up |
| 8a | Related Work — 3 hướng                | `RelatedWorkApproaches`  | 40 s | KG / Log-parse / LLM+RAG cards with limitations |
| 8b | Related Work — Timeline               | `RelatedWorkTimeline`    | 40 s | Methods plotted on axes; ~47% plateau line; PLLM point breaks ceiling |
| 9  | MEMRES — Lookup-First, LLM-Last       | `MemresPipeline`         | 60 s | 4 stages: Oracle, Hybrid, Clean, 6-level Cascade |
| 10 | Từ MEMRES đến CGAR — 3 lỗ hổng        | `MemresLimits`           | 45 s | 3 ALERT gaps **morph upward** into 3 SUCCESS fixes |
| 11 | CGAR — Paradigm Shift                 | `ParadigmShift`          | 35 s | Random brownian dots → constrained focused search |
| 12 | CGAR — Multi-Agent Loop ⭐            | `MultiAgentLoop`         | 70 s | 4 agents on ring + Session Store; full 2-iter algorithm trace (error → constraint flies in) |
| 13 | CGAR — Formulation as CSP ⭐          | `CSPFormulation`         | 60 s | P=⟨X,D,C⟩ color-coded + TransformMatchingTex; inset backtracking tree |
| 14 | Session-scoped Learning               | `SessionLearning`        | 40 s | 3 snippets write into shared ledger; counter ticks "rescued: 71" |
| 15 | Comprehensive Comparison (10 methods) | `PassRates`              | 60 s | Grouped bar chart, CGAR halo + ShowPassingFlash |
| 16 | HG2.9K — Error Breakdown              | `ErrorElim`              | 55 s | 4 error rows cross-out, count "1596 → 373" |
| 17 | GitChameleon — Open vs Closed         | `OpenVsClosed`           | 50 s | Two-column table (closed red / open green), CGAR row highlighted |
| 18 | Speed & Ablation                      | `SpeedRaceAndAblation`   | 60 s | Top: 3-bar race with `DecimalNumber` count-up; bottom: ablation shrink |
| 19 | Hạn chế — Hard Floor                  | `HardFloor`              | 40 s | Pie chart of 310 irreducible snippets |
| 20 | Architectural Limits                  | `ArchLimits`             | 30 s | 4 bullet cards |
| 21 | Hướng phát triển                      | `FutureWork`             | 35 s | 4 numbered cards |
| 22 | Tóm tắt & Kết luận                    | `Summary`                | 40 s | Headline numbers count-up |
| 23 | Thank you                             | `ThankYou`               | 25 s | Starfield reprise + glow |

⭐ = high-impact scene (3B1B-style animated algorithm + math morphs).

---

## Pacing rules

- Hold slide title 1.0–1.5 s before animation starts — viewer needs to anchor.
- Math/diagram reveals: 0.4–0.6 s per element, with `beat()` pauses between revelations.
- Count-up animations: 1.2–1.5 s — narrator timing room.
- No hard cuts between scenes; let `make concat` join them at the natural fades.
- Audio sync: narrator finishes a sentence → visual element appears (not the other way).

---

## Files

- `manim/style.py` — palette, fonts, helpers (`slide_chrome`, `glow`, `card`, `kbd`, `beat`, `starfield`, `count_up`, `code_panel`, ...).
- `manim/algorithms.py` — reusable algorithm mobjects (`DFSTreeAnimator`, `ConstraintLedger`, `AgentCard`, `AgentBus`, `MorphBar`).
- `manim/scenes.py` — 24 scene classes, 1-to-1 with the master timeline above.
- `renders/` — output (gitignored).
- `audio/` — narration mp3s, recorded later in NLE.

---

## Math + algorithm references

Style inspirations:
- 3blue1brown — dark BG, glow, `TransformMatchingTex` for equation mutation, `LaggedStart` for sequential reveal.
- `github.com/HarleyCoops/Math-To-Manim` — symbol-by-symbol math reveals, `Axes` + `ValueTracker` for live plots, highlighted active-step boxes.

Three scenes carry the full 3B1B-style algorithm narrative:
1. **`CSPFormulation`** — `P = ⟨X, D, C⟩` with color-coded letters, then expand each letter via `TransformFromCopy`; mutate `D(P_i)` formula symbol-by-symbol as constraints are added.
2. **`MultiAgentLoop`** — agents on a ring, build fail → error text morphs into a Constraint mobject that flies into the Session Store ledger; 2 iterations on-screen showing constraints accumulate.
3. **`RelatedWorkTimeline`** — `Axes` with `ValueTracker` for the ~47% plateau line; PLLM point pops above ceiling with `Indicate`.

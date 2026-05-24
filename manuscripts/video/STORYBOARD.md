# Storyboard — MEMRES & CGAR Presentation Video

**Duration:** ~10 min | **Aspect:** 16:9 1920×1080 | **FPS:** 30
**Pipeline:** Manim (2D math/diagrams/charts) + Blender (3D hero shots) → composited in DaVinci Resolve / ffmpeg
**Color palette (matches Metropolis beamer):** `mDarkTeal #23373B`, `mLightBrown #EB811B`, `softgray #F2F4F7`, success `#2E7D32`, alert `#C62828`

---

## Master timeline

| # | Slide topic | Time | Visual style | Tool | Scene file |
|---|---|---|---|---|---|
| 1 | Title card | 0:00–0:30 | 3D logo flythrough → 2D title | **Blender** → Manim | `blender/01_title_intro.py` + `manim/scenes.py::Title` |
| 2 | Outline (4 sections reveal) | 0:30–0:45 | 2D card stack reveal | Manim | `scenes.py::Outline` |
| 3 | FSE-AIWare problem (Input→Output) | 0:45–1:30 | Code panel → environment panel transform | Manim | `scenes.py::ProblemIO` |
| 4 | Requirements & Metrics | 1:30–2:00 | Constraint badges fly-in | Manim | `scenes.py::Requirements` |
| 5 | Datasets HG2.9K + GitChameleon | 2:00–2:30 | Two stacked card columns | Manim | `scenes.py::Datasets` |
| **6** | **Dependency Gap (DOMINO)** | **2:30–3:15** | **Domino chain knock-over, version arrows** | **Manim** ⭐ | `scenes.py::DependencyDomino` |
| 7 | MEMRES 4-stage pipeline + table | 3:15–3:45 | Horizontal pipeline reveal | Manim | `scenes.py::MemresPipeline` |
| 8 | MEMRES limitations → CGAR proposal | 3:45–4:15 | Red X on MEMRES → CGAR card slides in | Manim | `scenes.py::MemresLimits` |
| **9** | **CSP Formulation ⟨X,D,C⟩** | **4:15–5:00** | **Math tex build + variable highlight** | **Manim** ⭐ | `scenes.py::CSPFormulation` |
| **10** | **Backtracking algorithm** | **5:00–5:30** | **Search tree growing + branch pruning** | **Manim** ⭐ | `scenes.py::BacktrackingTree` |
| **11** | **CGAR 4-agent architecture** | **5:30–6:15** | **4 agent 3D figures with tool icons orbiting** | **Blender** ⭐ | `blender/11_agents.py` |
| 12 | Failure cases learned | 6:15–7:00 | Table rows with green/red highlight | Manim | `scenes.py::FailureCases` |
| **13** | **Pass rate + Speed bar race** | **7:00–8:00** | **Animated bar chart + counter race** | **Manim** ⭐⭐ | `scenes.py::PassRates`, `scenes.py::SpeedRace` |
| 14 | Errors eliminated + Ablation | 8:00–9:15 | 4 error categories crossed out + ablation bars | Manim | `scenes.py::ErrorElim`, `scenes.py::Ablation` |
| 15 | Thank you + QR + GitHub | 9:15–10:00 | Closing card, 3D camera pullback | Blender + Manim | `scenes.py::ThankYou` |

⭐ = high-impact scene worth extra polish.

---

## Pacing rules

- **Hold each slide title 1.0–1.5s before animation starts** — viewer needs to anchor.
- **Math/diagram reveals: 0.4–0.6s per element** (FadeIn + 0.5s wait).
- **Numbers in charts: count-up animation 1.5s** — gives narrator time to land the punchline.
- **Transitions between scenes:** crossfade 0.3s, no hard cuts (jarring on bar chart slides).
- **Audio sync:** narrator finishes a sentence → visual element appears (not the other way).

---

## Layer order (in compositor)

```
Layer 5  Subtitle bar (Vietnamese narration, optional)
Layer 4  Slide title chip (always top-left, persistent through scene)
Layer 3  Manim content (main work surface)
Layer 2  Blender 3D render (for slides 1, 11, 15)
Layer 1  Background gradient (softgray → white)
```

---

## What lives where

- `manim/scenes.py` — every Manim scene as a class. Render: `manim -pqh scenes.py SceneName`
- `manim/style.py` — shared colors, fonts, helpers (slide title, footer, bullet reveal)
- `blender/*.py` — standalone Blender scripts. Run via Blender MCP `execute_blender_code` OR `blender -b -P script.py`
- `renders/` — final mp4 per scene (gitignored, large)
- `audio/` — narration mp3 per slide if you record voiceover
- `Makefile` — `make all` renders every scene, `make scene-N` renders one

---

## Open questions for you

1. **Voiceover** — record yourself, or AI TTS (ElevenLabs/edge-tts)?
2. **Subtitles** — burn-in Vietnamese, English, or both?
3. **Length** — strict 10 min, or OK to run 12 min if visuals need breathing room?
4. **3D scope** — full 4-agent 3D scene for slide 11, or stick with stylized 2D Manim icons?

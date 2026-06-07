# Repository Structure

Single source of truth for "where do I find X?" in this repo.

## Top-level layout

```
fse-aiware-python-dependencies/         (repo root)
├── CLAUDE.md           ← project rules (12 working + G1-G10 research guardrails)
├── README.md           ← repo overview
├── STRUCTURE.md        ← THIS FILE — layout map
├── LICENSE
│
├── benchmarks/         ← DATASETS (frozen, do not modify)
├── tools/              ← FROZEN baseline tools (FSE'26 entries)
├── results/            ← per-tool, per-benchmark results
└── manuscripts/        ← paper drafts, slides, defense materials
```

> Active research code toward a future submission lives in a local-only
> workspace and is intentionally not tracked here. See README "Repository
> scope" for the rationale.

## Zones — frozen vs active

Two clearly separated zones. Do not let one bleed into the other.

| Zone | Paths | Rule |
|---|---|---|
| 🔒 **FROZEN** (end-of-term present + published baselines) | `manuscripts/slide/`, `manuscripts/slide-turn1/`, `manuscripts/video/`, `tools/{pllm,memres,cgar}/`, `benchmarks/` | Do **not** modify. Slides + video are the defended deliverable; tools + datasets are the published FSE'26 artifacts. |
| 🧪 **ACTIVE** (ongoing ICSE'27 research) | `research/icse27/` (local-only), `results/icse27/` | All new dependency-resolution method work happens here. Remote-GPU runtime lives in `research/icse27/deploy/`. |

## What lives where

### `benchmarks/`  (do not touch)

```
benchmarks/
├── hard-gists/                 ← HG2.9K (2891 snippets, gist hash dirs)
├── hard-gists.zip              ← compressed archive
└── gitchameleon-snippets/      ← 328 snippets (sample_N dirs) + ground_truth.csv
```

### `tools/`  (frozen baselines, do not modify per CLAUDE.md)

```
tools/
├── pllm/      ← Wang ASEW'25 — RAG + LLM iter (54.8% HG2.9K)
├── memres/    ← FSE'26 ours — memory-cascade resolver (87.2%)
└── cgar/      ← FSE'26 ours — constraint-guided agentic resolution (87.1%)
```

Each tool has its own `Dockerfile` and entry point. Do not edit; they are
the published baselines.

### `results/`  (all outputs, versioned)

```
results/
├── hg2k/
│   ├── pllm/csv/summary-all-runs.csv       ← PLLM published results
│   ├── memres/run_1/results.csv .. run_10/  ← MEMRES 10-run history
│   ├── cgar/results.csv                     ← CGAR published
│   ├── pyego/, readpy/                      ← additional baselines
│   └── ...
├── gitchameleon/
│   ├── pllm/results.csv
│   ├── memres/results.csv
│   └── cgar/results.csv
└── eval-subsets/cgar-rescue/                ← rescue eval data
```

### `manuscripts/`  (papers, slides, video)

```
manuscripts/
├── paper/               ← paper LaTeX source (locally only — see .gitignore)
├── slide/               ← slide decks (Beamer)
│   └── docs/DEFENSE_QA.md   ← defense question prep
├── submission/          ← final PDFs (locally only)
└── video/               ← presentation video pipeline (pure-Manim, 3Blue1Brown style)
    ├── Makefile             ← render orchestration
    ├── STORYBOARD.md        ← 24-scene mapping 1:1 with slide/main.tex
    ├── README.md            ← build guide
    ├── manim/
    │   ├── style.py            palette, helpers (glow, chip, count_up, …)
    │   ├── algorithms.py       reusable mobjects (DFSTreeAnimator,
    │   │                       ConstraintLedger, AgentCard/Bus, MorphBar)
    │   └── scenes.py           24 scene classes (Title … ThankYou)
    ├── renders/             ← outputs (locally only)
    │   ├── cgar_presentation.mp4   final concatenated video
    │   └── videos/scenes/1080p60/  per-scene HD mp4s
    └── audio/               ← narration (recorded later in NLE)
```

## How to find things

| If you want to... | Look here |
|---|---|
| Find baseline tool sources | `tools/{pllm,memres,cgar}/` |
| Find baseline results | `results/hg2k/<tool>/` or `results/gitchameleon/<tool>/` |
| Read project rules | `CLAUDE.md` |
| Read defense Q&A | `manuscripts/slide/docs/DEFENSE_QA.md` |
| Read video storyboard | `manuscripts/video/STORYBOARD.md` |

## Running the baseline tools

Each tool under `tools/` has its own `Dockerfile` and `README.md`. Typical
flow:

```bash
cd tools/cgar
docker compose -f docker-compose-gitchameleon.yml up --build -d
# Results: results/gitchameleon/cgar/results.csv
```

See the per-tool README for full instructions.

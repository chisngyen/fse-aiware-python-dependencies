# CGAR presentation video — build guide

Pure-Manim, 3blue1brown-style video for the MEMRES & CGAR project. Mirrors `../slide/main.tex` slide-by-slide (~15-18 min, 24 scenes).

## Layout

```
video/
├── STORYBOARD.md       slide → scene mapping (read this first)
├── manim/
│   ├── style.py        palette, fonts, helpers
│   ├── algorithms.py   reusable algorithm mobjects (DFS tree, ledger, agents)
│   └── scenes.py       24 scene classes (Title … ThankYou)
├── renders/            output (gitignored)
├── audio/              narration mp3s if you record voiceover later
└── Makefile            render orchestration
```

## Prerequisites

```
pip install manim         # tested with manim 0.20.x
ffmpeg                    # in PATH for `make concat`
```

LaTeX is required for `MathTex` / `Tex` (one of: MikTeX, TeX Live). On Windows MikTeX auto-installs missing packages.

## Iterate on one scene

```
make preview SCENE=MultiAgentLoop    # 480p15, fast
make hd      SCENE=MultiAgentLoop    # 1080p60, final
make list                            # show all scene names
```

## Render the final cut

```
make all                # every scene at 1080p60 (long — coffee break)
make concat             # ffmpeg-concat → renders/cgar_presentation.mp4
```

## Adding narration (WAV-driven "wait-play")

The scenes render silent on purpose. Narration is muxed in afterward by
`build_narrated.py` — no re-render. Each scene plays its animation, then freezes
the last frame until its narration finishes, then cuts to the next scene.

1. Generate **one WAV per scene** (local TTS, no API) from the script in
   `audio/narration_vi.md`, naming each file `audio/NN_scenename.wav` where
   `NN` is the scene number and `scenename` is the scene class lowercased:
   `01_title.wav`, `02_outline.wav`, `03_context.wav`, `04_problemio.wav`, …,
   `24_thankyou.wav`. (`.mp3` is accepted as a fallback.)
2. Build the narrated cut:

   ```
   make narrate                 # → renders/cgar_presentation_narrated.mp4
   python build_narrated.py --check   # verify all 24 WAVs exist, build nothing
   ```

`build_narrated.py` freezes the last frame (`tpad`) when narration is longer
than the animation and pads silence (`apad`) when it is shorter, then concats.
It uses the imageio_ffmpeg v7.1 binary by default (override with `FFMPEG_BIN`);
the iGameCenter 2017 ffmpeg lacks `tpad` and will not work.

Burn subtitles in an NLE afterward if needed (Vietnamese narration with English
technical terms).

## Style guide

- Background: `#0E1518` (near-black, 3B1B-style).
- Accent: `#EB811B` (warm orange).
- Typography: DejaVu Sans for body, DejaVu Sans Mono for code.
- Math: `MathTex` with color-coded variable letters.
- Morph transforms used at: slide 5 (import → constraint), slide 10 (gap → fix), slide 12 (error → constraint), slide 13 (formula mutation).
- No 3D camera flythroughs. All depth is simulated via `glow()` + gradient `deep_box()`.

## Verification

- `make list` should show 24 scenes in narrative order.
- `make preview SCENE=Name` should render cleanly for every name.
- No file in this directory should reference Blender (`git grep -i blender`).

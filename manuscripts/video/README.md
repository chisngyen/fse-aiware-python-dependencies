# CGAR Presentation Video — Build Guide

Source for a ~10-min presentation video for the MEMRES & CGAR project. Mirrors
the structure of `../main_v2.tex` slide-by-slide.

## Layout

```
video/
├── STORYBOARD.md       slide → scene → tool mapping (read this first)
├── manim/
│   ├── style.py        shared palette, fonts, helpers
│   └── scenes.py       all 16 scenes (Title … ThankYou)
├── blender/
│   ├── 01_title_intro.py  3D wreckage flythrough for slide 1
│   └── 11_agents.py       4-agent orbit shot for slide 11
├── renders/            output (gitignored)
├── audio/              narration mp3s if you record voiceover
└── Makefile            render orchestration
```

## Prerequisites

```bash
pip install manim   # already verified: 0.20.1
# Blender 4.x on PATH (only needed for slides 1 + 11; everything else is Manim)
# ffmpeg on PATH (Manim ships with one; system one needed for `make concat`)
```

## Iterate fast on one scene

```bash
make preview SCENE=DependencyDomino     # 480p15, ~5s render
```

Browse all scene names:

```bash
make list
```

## Render the final cut

```bash
make all          # every Manim scene at 1080p60
make blender-11   # 4-agent 3D shot (run Blender separately first if you want preview)
make concat       # ffmpeg-concat → renders/cgar_presentation.mp4
```

## Blender via MCP (interactive)

If you want to iterate the 3D shots inside the Blender GUI while talking to
Claude:

1. Open Blender.
2. Install + enable the Blender-MCP addon, click **Start MCP Server**.
3. Paste the body of `blender/11_agents.py` into a Claude message asking
   "execute this in Blender" — it goes through `mcp__blender__execute_blender_code`.

This rebuilds the scene live so you can adjust framing, lighting, camera path
without re-rendering.

## Recording voiceover (optional)

The script lives at `../script.md`. Suggested flow:

1. Record one mp3 per slide into `audio/NN_slidename.mp3`.
2. In DaVinci Resolve / Premiere, drop the rendered mp4 scenes onto the
   timeline, then sync each audio clip.
3. Burn subtitles via ffmpeg if needed.

Or use edge-tts for a quick draft narration:

```bash
edge-tts --voice vi-VN-HoaiMyNeural \
  --file ../script.md --write-media audio/full_draft.mp3
```

## Render-time benchmarks (reference, M2-class laptop)

| Scene             | -ql (480p15) | -qh (1080p60) |
|-------------------|--------------|---------------|
| Title             | ~4 s         | ~25 s         |
| DependencyDomino  | ~12 s        | ~90 s         |
| BacktrackingTree  | ~10 s        | ~75 s         |
| SpeedRace         | ~6 s         | ~40 s         |
| Blender 11_agents | —            | ~8 min (240 fr Cycles 64 spp) |

## Composite layer order (in NLE)

```
5  Vietnamese / English subtitles
4  Persistent slide title chip + page chip      (Manim chrome)
3  Manim main scene content                      (most slides)
2  Blender 3D backdrop / hero                    (slides 1, 11, 15)
1  Background gradient softgray → white
```

## Open decisions

See bottom of `STORYBOARD.md` — pick voiceover source, subtitle language,
strict-10-min vs. 12-min, and Blender-vs-Manim for slide 11.

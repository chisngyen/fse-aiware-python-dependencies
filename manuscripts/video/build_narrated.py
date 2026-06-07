#!/usr/bin/env python3
"""Build the narrated "wait-play" cut of the CGAR presentation.

For every scene (in narrative order) we mux its pre-rendered 1080p60 clip with
its narration WAV.  When the narration is longer than the animation, the last
video frame is frozen (`tpad`) until the narration finishes, then we cut to the
next scene.  When the narration is shorter, the audio is padded with trailing
silence (`apad`).  Each segment is re-encoded to a uniform codec so the final
concat can stream-copy.

Visuals are finalized — this script never re-renders Manim.

Usage:
    python build_narrated.py            # build renders/cgar_presentation_narrated.mp4
    python build_narrated.py --check    # only verify every WAV exists, build nothing

Audio file naming (one per scene): audio/{NN}_{scene_lowercased}.wav
e.g. ProblemIO -> audio/04_problemio.wav   (.mp3 accepted as a fallback)

ffmpeg: defaults to the imageio_ffmpeg v7.1 binary (has tpad+apad). Override
with the FFMPEG_BIN env var. The iGameCenter 2017 build lacks tpad; do not use.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import wave
from pathlib import Path

# Scene order — must match the SCENES list in the Makefile / STORYBOARD timeline.
SCENES = [
    "Title", "Outline", "Context", "ProblemIO", "DependencyDomino",
    "CombinatorialExplosion", "Datasets", "RelatedWorkApproaches", "RelatedWorkTimeline",
    "MemresPipeline", "MemresLimits", "ParadigmShift", "MultiAgentLoop",
    "CSPFormulation", "SessionLearning", "PassRates", "ErrorElim",
    "OpenVsClosed", "SpeedRaceAndAblation", "HardFloor", "ArchLimits",
    "FutureWork", "Summary", "ThankYou",
]

HERE = Path(__file__).resolve().parent
VIDEO_DIR = HERE / "renders" / "videos" / "scenes" / "1080p60"
AUDIO_DIR = HERE / "audio"
SEG_DIR = HERE / "renders" / "segments"
OUT = HERE / "renders" / "cgar_presentation_narrated.mp4"

_DUR_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def ffmpeg_bin() -> str:
    """Resolve a tpad-capable ffmpeg. Prefer FFMPEG_BIN, else imageio_ffmpeg v7.1."""
    env = os.environ.get("FFMPEG_BIN")
    if env:
        return env
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # pragma: no cover - environment dependent
        return "ffmpeg"  # last resort; must be a build with tpad


def audio_path(idx: int, scene: str) -> Path | None:
    """Locate the narration file for a scene: .wav preferred, .mp3 fallback."""
    stem = f"{idx:02d}_{scene.lower()}"
    for ext in (".wav", ".mp3"):
        p = AUDIO_DIR / f"{stem}{ext}"
        if p.exists():
            return p
    return None


def wav_duration(path: Path) -> float:
    """Exact WAV duration via the stdlib (no ffprobe needed)."""
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def media_duration(ffmpeg: str, path: Path) -> float:
    """Duration of any media file by parsing ffmpeg's `Duration:` banner."""
    if path.suffix.lower() == ".wav":
        return wav_duration(path)
    proc = subprocess.run([ffmpeg, "-i", str(path)],
                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    m = _DUR_RE.search(proc.stderr)
    if not m:
        raise RuntimeError(f"Could not parse duration from ffmpeg for {path}")
    h, mm, ss = m.groups()
    return int(h) * 3600 + int(mm) * 60 + float(ss)


def resolve_scenes() -> list[tuple[int, str, Path, Path]]:
    """Return (idx, scene, video, audio) for all scenes, failing loud on gaps."""
    missing_video, missing_audio, rows = [], [], []
    for i, scene in enumerate(SCENES, start=1):
        vid = VIDEO_DIR / f"{scene}.mp4"
        aud = audio_path(i, scene)
        if not vid.exists():
            missing_video.append(f"  {i:02d} {scene}: {vid}")
        if aud is None:
            missing_audio.append(f"  {i:02d} {scene}: audio/{i:02d}_{scene.lower()}.wav")
        if vid.exists() and aud is not None:
            rows.append((i, scene, vid, aud))
    if missing_video or missing_audio:
        if missing_video:
            print("MISSING rendered video clips:", *missing_video, sep="\n", file=sys.stderr)
        if missing_audio:
            print("MISSING narration audio:", *missing_audio, sep="\n", file=sys.stderr)
        print(f"\nFAIL: {len(missing_video)} video + {len(missing_audio)} audio "
              f"file(s) missing; nothing built.", file=sys.stderr)
        sys.exit(1)
    return rows


def build_segment(ffmpeg: str, idx: int, scene: str, vid: Path, aud: Path) -> tuple[Path, float, float, float]:
    """Mux one scene; freeze last frame if narration is longer. Returns segment + durations."""
    vdur = media_duration(ffmpeg, vid)
    adur = wav_duration(aud) if aud.suffix.lower() == ".wav" else media_duration(ffmpeg, aud)
    target = max(vdur, adur)
    freeze = max(0.0, target - vdur)
    seg = SEG_DIR / f"{idx:02d}_{scene}.mp4"
    filt = (f"[0:v]tpad=stop_mode=clone:stop_duration={freeze:.3f}[v];"
            f"[1:a]apad=whole_dur={target:.3f}[a]")
    cmd = [ffmpeg, "-y", "-loglevel", "error",
           "-i", str(vid), "-i", str(aud),
           "-filter_complex", filt,
           "-map", "[v]", "-map", "[a]", "-t", f"{target:.3f}",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "60",
           "-c:a", "aac", "-ar", "48000",
           str(seg)]
    subprocess.run(cmd, check=True)
    return seg, vdur, adur, target


def main() -> None:
    check_only = "--check" in sys.argv[1:]
    rows = resolve_scenes()  # exits if anything missing
    if check_only:
        print(f"OK: all {len(rows)} scenes have a rendered clip and narration file.")
        return

    ffmpeg = ffmpeg_bin()
    SEG_DIR.mkdir(parents=True, exist_ok=True)

    print(f"{'#':>2}  {'scene':24} {'video':>7} {'audio':>7} {'freeze':>7} {'target':>7}")
    segments, total = [], 0.0
    for idx, scene, vid, aud in rows:
        seg, vdur, adur, target = build_segment(ffmpeg, idx, scene, vid, aud)
        segments.append(seg)
        total += target
        print(f"{idx:>2}  {scene:24} {vdur:6.1f}s {adur:6.1f}s "
              f"{max(0.0, target - vdur):6.1f}s {target:6.1f}s")

    seglist = SEG_DIR / "seglist.txt"
    seglist.write_text(
        "".join(f"file '{s.as_posix()}'\n" for s in segments), encoding="utf-8")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error",
                    "-f", "concat", "-safe", "0", "-i", str(seglist),
                    "-c", "copy", str(OUT)], check=True)

    mins, secs = divmod(int(round(total)), 60)
    print(f"\n==> {OUT}  (~{mins}:{secs:02d}, {len(segments)} scenes)")


if __name__ == "__main__":
    main()

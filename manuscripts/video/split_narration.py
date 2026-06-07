#!/usr/bin/env python3
"""Split ONE long narration WAV into 24 per-scene WAVs via forced alignment.

You generate a single audio file (TTS the whole script in one go, no pauses
needed). This script transcribes it with faster-whisper (word timestamps),
aligns the recognised words against the known 24 scene transcripts in
`audio/txt/NN_scenename.txt`, finds each scene boundary, snaps the cut to the
nearest silence, and writes `audio/NN_scenename.wav` — the exact names
`build_narrated.py` expects.

Boundaries are taken at the FIRST words of each scene (clean Vietnamese
phrases), so mis-transcribed English terms (scipy, AttributeError) inside a
scene do not affect where we cut.

Usage:
    python split_narration.py path/to/narration_full.wav
    python split_narration.py narration_full.wav --model medium   # better VI accuracy

After it runs:
    python build_narrated.py --check   # should now find all 24 WAVs
    make narrate
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
TXT_DIR = HERE / "audio" / "txt"
OUT_DIR = HERE / "audio"

SCENES = [
    "Title", "Outline", "Context", "ProblemIO", "DependencyDomino",
    "CombinatorialExplosion", "Datasets", "RelatedWorkApproaches", "RelatedWorkTimeline",
    "MemresPipeline", "MemresLimits", "ParadigmShift", "MultiAgentLoop",
    "CSPFormulation", "SessionLearning", "PassRates", "ErrorElim",
    "OpenVsClosed", "SpeedRaceAndAblation", "HardFloor", "ArchLimits",
    "FutureWork", "Summary", "ThankYou",
]


def ffmpeg_bin() -> str:
    import os
    if os.environ.get("FFMPEG_BIN"):
        return os.environ["FFMPEG_BIN"]
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def norm_token(tok: str) -> str:
    """Lowercase, drop punctuation, keep Vietnamese letters/digits."""
    tok = unicodedata.normalize("NFC", tok).lower()
    tok = re.sub(r"[^0-9a-zà-ỹ]+", "", tok)
    return tok


def tokenize(text: str) -> list[str]:
    return [t for t in (norm_token(w) for w in text.split()) if t]


def load_scene_tokens() -> tuple[list[str], list[int]]:
    """Concatenated reference tokens + the token index where each scene starts."""
    ref: list[str] = []
    starts: list[int] = []
    for i, scene in enumerate(SCENES, start=1):
        p = TXT_DIR / f"{i:02d}_{scene.lower()}.txt"
        if not p.exists():
            sys.exit(f"FAIL: missing transcript {p} (run extract_narration.py first)")
        starts.append(len(ref))
        ref.extend(tokenize(p.read_text(encoding="utf-8")))
    return ref, starts


def transcribe(wav: Path, model_name: str) -> list[tuple[str, float]]:
    """Return [(normalized_word, start_time)] from faster-whisper."""
    from faster_whisper import WhisperModel
    try:
        import torch
        cuda = torch.cuda.is_available()
    except Exception:
        cuda = False
    device = "cuda" if cuda else "cpu"
    compute = "float16" if cuda else "int8"
    print(f"[whisper] model={model_name} device={device} ...", flush=True)
    model = WhisperModel(model_name, device=device, compute_type=compute)
    segments, _ = model.transcribe(str(wav), language="vi", word_timestamps=True)
    words: list[tuple[str, float]] = []
    for seg in segments:
        for w in (seg.words or []):
            n = norm_token(w.word)
            if n:
                words.append((n, float(w.start)))
    if not words:
        sys.exit("FAIL: whisper returned no words — check the audio file.")
    print(f"[whisper] {len(words)} words recognised.")
    return words


def boundary_times(ref: list[str], starts: list[int],
                   asr: list[tuple[str, float]], audio_end: float) -> list[float]:
    """Map each scene-start ref index to an ASR word start time."""
    asr_tokens = [w for w, _ in asr]
    asr_time = [t for _, t in asr]
    sm = difflib.SequenceMatcher(None, ref, asr_tokens, autojunk=False)
    ref2asr: dict[int, int] = {}
    for i1, j1, n in sm.get_matching_blocks():
        for k in range(n):
            ref2asr[i1 + k] = j1 + k

    sorted_ref_idx = sorted(ref2asr)
    bounds = [0.0]  # scene 1 always starts at 0
    for b in starts[1:]:
        # nearest matched ref token at or after the scene start
        anchor = next((r for r in sorted_ref_idx if r >= b), None)
        if anchor is None:
            # proportional fallback
            bounds.append(audio_end * b / max(1, len(ref)))
            continue
        bounds.append(asr_time[ref2asr[anchor]])
    # enforce strictly increasing, clamp into (0, audio_end)
    for i in range(1, len(bounds)):
        bounds[i] = min(max(bounds[i], bounds[i - 1] + 0.05), audio_end - 0.05)
    return bounds


def snap_to_silence(wav: Path, bounds: list[float], ffmpeg: str) -> list[float]:
    """Move each interior boundary to the middle of the nearest silence (±0.5s)."""
    try:
        from pydub import AudioSegment, silence
        AudioSegment.converter = ffmpeg
        audio = AudioSegment.from_file(str(wav))
    except Exception as e:
        print(f"[snap] skipped (pydub/ffmpeg: {e}); using raw boundaries.")
        return bounds
    sil = silence.detect_silence(audio, min_silence_len=120, silence_thresh=audio.dBFS - 16)
    sil = [((a + b) / 2000.0) for a, b in sil]  # ms midpoints -> seconds
    snapped = [bounds[0]]
    for t in bounds[1:]:
        near = [s for s in sil if abs(s - t) <= 0.5]
        snapped.append(min(near, key=lambda s: abs(s - t)) if near else t)
    return snapped


def audio_duration(path: Path) -> float:
    """Duration in seconds. WAV via stdlib; other formats (mp3) via ffmpeg."""
    if path.suffix.lower() == ".wav":
        import wave as wavemod
        with wavemod.open(str(path), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    import re as _re, subprocess
    proc = subprocess.run([ffmpeg_bin(), "-i", str(path)],
                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    m = _re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
    if not m:
        raise RuntimeError(f"Could not parse duration for {path}")
    h, mm, ss = m.groups()
    return int(h) * 3600 + int(mm) * 60 + float(ss)


def cut(ffmpeg: str, wav: Path, bounds: list[float], end: float) -> None:
    import subprocess
    print(f"\n{'#':>2}  {'scene':24} {'start':>8} {'end':>8} {'dur':>7}")
    edges = bounds + [end]
    for i, scene in enumerate(SCENES):
        s, e = edges[i], edges[i + 1]
        out = OUT_DIR / f"{i+1:02d}_{scene.lower()}.wav"
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(wav),
                        "-ss", f"{s:.3f}", "-to", f"{e:.3f}",
                        "-c:a", "pcm_s16le", "-ac", "1", str(out)], check=True)
        print(f"{i+1:>2}  {scene:24} {s:7.2f}s {e:7.2f}s {e-s:6.2f}s")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", help="single long narration WAV")
    ap.add_argument("--model", default="small", help="faster-whisper model (small/medium/large-v3)")
    args = ap.parse_args()

    wav = Path(args.wav)
    if not wav.exists():
        sys.exit(f"FAIL: {wav} not found")

    ref, starts = load_scene_tokens()
    end = audio_duration(wav)
    asr = transcribe(wav, args.model)
    bounds = boundary_times(ref, starts, asr, end)
    bounds = snap_to_silence(wav, bounds, ffmpeg_bin())
    cut(ffmpeg_bin(), wav, bounds, end)
    print(f"\n==> wrote 24 WAVs to {OUT_DIR}.  Next: python build_narrated.py --check")


if __name__ == "__main__":
    main()

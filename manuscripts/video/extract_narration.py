#!/usr/bin/env python3
"""Extract plain-text narration (one .txt per scene) from narration_vi.md.

Each scene section in narration_vi.md looks like:

    ## 04 · ProblemIO — [0:19-0:26] (~7s)
    `audio/04_problemio.mp3`

    > spoken line 1
    > spoken line 2

    *(~14s ...)*

We pull only the `>` quote lines, join them into one paragraph, and write
`audio/txt/NN_scenename.txt` — ready to feed into any text-to-speech tool.
Output filenames match the WAV names build_narrated.py expects.

Usage:  python extract_narration.py
"""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "audio" / "narration_vi.md"
OUT_DIR = HERE / "audio" / "txt"

HEADER_RE = re.compile(r"^##\s*(\d+)\s*·\s*(\w+)")


def main() -> None:
    lines = SRC.read_text(encoding="utf-8").splitlines()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sections: list[tuple[int, str, list[str]]] = []
    cur: tuple[int, str] | None = None
    quote: list[str] = []
    for line in lines:
        m = HEADER_RE.match(line)
        if m:
            if cur is not None:
                sections.append((cur[0], cur[1], quote))
            cur = (int(m.group(1)), m.group(2))
            quote = []
        elif cur is not None and line.startswith(">"):
            quote.append(line[1:].strip())
    if cur is not None:
        sections.append((cur[0], cur[1], quote))

    written = 0
    for idx, scene, quote_lines in sections:
        text = " ".join(q for q in quote_lines if q).strip()
        if not text:
            print(f"  WARN: no spoken text for {idx:02d} {scene}")
            continue
        path = OUT_DIR / f"{idx:02d}_{scene.lower()}.txt"
        path.write_text(text + "\n", encoding="utf-8")
        written += 1
    print(f"Wrote {written} narration .txt files to {OUT_DIR}")


if __name__ == "__main__":
    main()

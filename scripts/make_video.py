#!/usr/bin/env python3
"""
make_video.py — one-command local AI video pipeline.

Turns a STUDENT/TEACHER beat-script (JSON) directly into a finished
1080x1920 vertical video, like the "Peter Brain Riot"-style reaction skits:

    beat script -> per-beat diagrams + dual-voice narration
                 -> final_video.mp4 with burned-in captions over a looping background

Steps run in order:
    1. generate_lesson_audio.py  per-line TTS wavs + manifest.json
    2. make_diagrams.py          beat01.png .. beatNN.png
    3. assemble_video.py         final_video.mp4

Usage:
    python3 make_video.py script.json out_dir/ \
        --background background_loop.mp4 \
        --font /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf

All intermediate files (lines/, diagrams/, narration, manifest, video)
land inside out_dir/.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from generate_lesson_audio import SILENCE_BETWEEN_LINES_SEC

ROOT = Path(__file__).resolve().parents[1]   # repo root (local-video-ai/)
SCRIPTS_DIR = ROOT / "scripts"


def run(step: str, cmd: list[str]) -> None:
    print(f"\n=== {step} ===")
    subprocess.run(cmd, cwd=ROOT, check=True)


def main():
    ap = argparse.ArgumentParser(description="One-command local AI video pipeline")
    ap.add_argument("script", help="beat-script JSON (topic + beats)")
    ap.add_argument("out_dir", help="output directory (e.g. output/shm_video)")
    ap.add_argument("--background", required=True, help="loopable background video (1080x1920)")
    ap.add_argument("--font", required=True, help="path to a bold sans-serif .ttf")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    args = ap.parse_args()

    script = Path(args.script)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    gap_sec = SILENCE_BETWEEN_LINES_SEC

    run(
        "Generating narration + manifest",
        [sys.executable, str(SCRIPTS_DIR / "generate_lesson_audio.py"), str(script), str(out_dir)],
    )

    run(
        "Generating beat diagrams",
        [
            sys.executable, str(SCRIPTS_DIR / "make_diagrams.py"), str(script),
            str(out_dir / "diagrams"), "--width", str(args.width), "--height", str(args.height),
        ],
    )

    run(
        "Assembling final video",
        [
            sys.executable, str(SCRIPTS_DIR / "assemble_video.py"),
            "--manifest", str(out_dir / "manifest.json"),
            "--audio-dir", str(out_dir),
            "--diagrams-dir", str(out_dir / "diagrams"),
            "--background", str(args.background),
            "--font", str(args.font),
            "--gap-sec", str(gap_sec),
            "--width", str(args.width),
            "--height", str(args.height),
            "--out", str(out_dir / "final_video.mp4"),
        ],
    )

    print(f"\nDone: {out_dir / 'final_video.mp4'}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
make_video.py — one-command local AI video pipeline.

Turns a STUDENT/TEACHER beat-script (JSON) directly into a finished
1080x1920 vertical video, like the "Peter Brain Riot"-style reaction skits:

    beat script -> per-beat diagrams + dual-voice narration
                 -> final video with burned-in captions over a looping background

Steps run in order:
    1. generate_lesson_audio.py  per-line TTS wavs + manifest.json
    2. make_diagrams.py          beat01.png .. beatNN.png
    3. assemble_video.py         final video

Conventions:
    - intermediates (manifest.json, lines/, diagrams/) live in the project
      folder that holds the beat script, e.g. input/shm/script.json ->
      input/shm/{manifest.json, lines/, diagrams/}
    - the final video lands in output/, e.g. output/shm_final_video.mp4

Usage:
    python3 make_video.py input/shm/script.json \
        --background assets/bg/background_loop.mp4 \
        --font /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
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


def project_name(script: Path) -> str:
    """Derive a project folder name from the script's location.

    input/shm/script.json -> "shm"  (preferred layout)
    content/shm_script.json -> "shm_script"
    """
    parent_dir = script.parent
    if parent_dir.parent.name == "input":
        return parent_dir.name
    return script.stem


def main():
    ap = argparse.ArgumentParser(description="One-command local AI video pipeline")
    ap.add_argument("script", help="beat-script JSON (topic + beats), e.g. input/shm/script.json")
    ap.add_argument("--background", required=True, help="loopable background video (1080x1920)")
    ap.add_argument("--font", required=True, help="path to a bold sans-serif .ttf")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--work-dir", help="project folder for intermediates (default: script's parent dir)")
    ap.add_argument("--output", help="final video path (default: output/<project>_final_video.mp4)")
    args = ap.parse_args()

    script = Path(args.script).resolve()
    gap_sec = SILENCE_BETWEEN_LINES_SEC

    work_dir = Path(args.work_dir).resolve() if args.work_dir else script.parent
    work_dir.mkdir(parents=True, exist_ok=True)

    out_video = Path(args.output).resolve() if args.output else ROOT / "output" / f"{project_name(script)}_final_video.mp4"
    out_video.parent.mkdir(parents=True, exist_ok=True)

    run(
        "Generating narration + manifest",
        [sys.executable, str(SCRIPTS_DIR / "generate_lesson_audio.py"), str(script), str(work_dir)],
    )

    run(
        "Generating beat diagrams",
        [
            sys.executable, str(SCRIPTS_DIR / "make_diagrams.py"), str(script),
            str(work_dir / "diagrams"), "--width", str(args.width), "--height", str(args.height),
        ],
    )

    run(
        "Assembling final video",
        [
            sys.executable, str(SCRIPTS_DIR / "assemble_video.py"),
            "--manifest", str(work_dir / "manifest.json"),
            "--audio-dir", str(work_dir),
            "--diagrams-dir", str(work_dir / "diagrams"),
            "--background", str(args.background),
            "--font", str(args.font),
            "--gap-sec", str(gap_sec),
            "--width", str(args.width),
            "--height", str(args.height),
            "--out", str(out_video),
        ],
    )

    print(f"\nDone: {out_video}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
main.py — single CLI entry point for the local-video-ai toolkit.

Chains transcription (faster-whisper) and TTS (Piper) behind one command,
and can batch-process every video under input/ into per-video subfolders
in output/<video-name>/.

Usage:
    python3 main.py input/video.mp4                        # transcribe one file
    python3 main.py input/video.mp4 --tts content/tts_test.txt   # + TTS
    python3 main.py --batch                                 # all media in input/

All settings (whisper model/language/format, piper model, data dir) come
from config/app.env (see config/app.env.example).
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

from config import load_config  # noqa: E402

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
MEDIA_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4a", ".mp3", ".wav", ".flac", ".ogg"}
CONFIG = ROOT / "config" / "app.env"


def die(msg: str) -> None:
    print(f"main.py: {msg}", file=sys.stderr)
    sys.exit(1)


def transcribe(video: Path, model: str, language: str, out_dir: Path) -> None:
    cmd = [
        sys.executable, str(SCRIPTS / "transcribe.py"),
        str(video), "--model", model, "--language", language,
        "--output_dir", str(out_dir),
    ]
    print(f"[transcribe] {video.name} -> {out_dir}")
    subprocess.run(cmd, check=True)


def run_tts(text_file: Path, model: str) -> None:
    out_wav = ROOT / "output" / f"{text_file.stem}.wav"
    cmd = [sys.executable, str(SCRIPTS / "tts.py"), str(text_file), str(out_wav), "--model", model]
    print(f"[tts] {text_file.name} -> {out_wav}")
    subprocess.run(cmd, cwd=ROOT, check=True)


def find_media(root: Path) -> list[Path]:
    files = []
    for ext in MEDIA_EXTS:
        files.extend(root.rglob(f"*{ext}"))
    skip_dir = {"lines", "diagrams", "output"}
    return sorted(m for m in files
                  if not any(part in skip_dir for part in m.parent.parts))


def main():
    ap = argparse.ArgumentParser(description="Local video AI entry point")
    ap.add_argument("video", nargs="?", help="video/audio file to transcribe")
    ap.add_argument("--batch", action="store_true",
                    help="transcribe every media file under input/ (skips beat-script dirs)")
    ap.add_argument("--tts", metavar="TEXT_FILE",
                    help="also synthesize a Piper voiceover for a text file")
    args = ap.parse_args()

    if not CONFIG.exists():
        print(f"warning: {CONFIG} not found — copying example; edit it as needed")
        Path(CONFIG).write_text((ROOT / "config" / "app.env.example").read_text())

    if args.video:
        video = Path(args.video)
        if not video.exists():
            die(f"video not found: {video}")
        cfg = load_config()
        transcribe(video, cfg["WHISPER_MODEL"], cfg["WHISPER_LANGUAGE"],
                   ROOT / "output" / video.stem)
    elif args.batch:
        cfg = load_config()
        media = find_media(ROOT / "input")
        if not media:
            die("no media files (mp4/mov/mkv/webm/m4a/mp3/wav/flac/ogg) found under input/")
        print(f"[batch] found {len(media)} media file(s)")
        for i, video in enumerate(media, start=1):
            print(f"\n[{i}/{len(media)}] {video}")
            transcribe(video, cfg["WHISPER_MODEL"], cfg["WHISPER_LANGUAGE"],
                       ROOT / "output" / video.stem)
    else:
        die("provide a video file or use --batch (see --help)")

    if args.tts:
        run_tts(Path(args.tts), load_config()["PIPER_MODEL"])

    print("\nAll done.")


if __name__ == "__main__":
    main()
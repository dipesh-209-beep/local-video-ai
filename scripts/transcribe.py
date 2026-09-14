#!/usr/bin/env python3
"""
transcribe.py — faster-whisper transcription with openai-whisper-compatible
output formats (txt / srt / vtt / tsv / json).

Runs on CPU via CTranslate2 (int8) — several times faster than openai-whisper
on CPU while producing the same segment-level results.

Usage:
    python3 scripts/transcribe.py input/video.mp4 --output_dir output/video-name
    python3 scripts/transcribe.py input/video.mp4 --model base --language en

Writes:
    output/video-name/video-name.{txt,srt,vtt,tsv,json}
"""

import argparse
import json
import sys
from pathlib import Path

from config import load_config

cfg = load_config()


def die(msg: str) -> None:
    print(f"transcribe.py: {msg}", file=sys.stderr)
    sys.exit(1)


def format_timestamp(seconds: float, srt: bool = False) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, msec = divmod(rem, 1000)
    if srt:
        return f"{h:02d}:{m:02d}:{s:02d},{msec:03d}"
    return f"{h:02d}:{m:02d}:{s:02d}.{msec:03d}"


def write_outputs(segments, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    segs = list(segments)   # materialize: faster-whisper yields a generator

    txt = "\n".join(s.text.strip() for s in segs)
    (out_dir / f"{stem}.txt").write_text(txt + "\n", encoding="utf-8")

    srt_lines = []
    vtt_lines = ["WEBVTT\n"]
    tsv_lines = ["start\tend\ttext"]
    json_segments = []

    for i, seg in enumerate(segs, start=1):
        text = seg.text.strip()
        srt_lines.append(f"{i}\n{format_timestamp(seg.start, srt=True)} --> "
                         f"{format_timestamp(seg.end, srt=True)}\n{text}\n")
        vtt_lines.append(f"{format_timestamp(seg.start)} --> {format_timestamp(seg.end)}\n{text}\n")
        tsv_lines.append(f"{seg.start:.3f}\t{seg.end:.3f}\t{text}")
        json_segments.append({"id": i, "start": round(seg.start, 3),
                              "end": round(seg.end, 3), "text": text})

    (out_dir / f"{stem}.srt").write_text("\n".join(srt_lines), encoding="utf-8")
    (out_dir / f"{stem}.vtt").write_text("\n".join(vtt_lines), encoding="utf-8")
    (out_dir / f"{stem}.tsv").write_text("\n".join(tsv_lines) + "\n", encoding="utf-8")
    (out_dir / f"{stem}.json").write_text(json.dumps(json_segments, indent=2), encoding="utf-8")

    return out_dir


def main():
    ap = argparse.ArgumentParser(description="faster-whisper transcription")
    ap.add_argument("video", help="video or audio file to transcribe")
    ap.add_argument("--model", default=cfg["WHISPER_MODEL"],
                    help=f"whisper model size (default: {cfg['WHISPER_MODEL']})")
    ap.add_argument("--language", default=cfg["WHISPER_LANGUAGE"],
                    help=f"language code (default: {cfg['WHISPER_LANGUAGE']})")
    ap.add_argument("--output_dir", help="output dir (default: output/<video-name>/)")
    args = ap.parse_args()

    video = Path(args.video).resolve()
    if not video.exists():
        die(f"video not found: {video}")

    out_dir = Path(args.output_dir).resolve() if args.output_dir \
        else (Path(__file__).resolve().parents[1] / "output" / video.stem)

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        die("faster-whisper is not installed — run '.venv/bin/pip install -r requirements.txt'")

    print(f"Loading {args.model} model (CPU/int8)…")
    model = WhisperModel(args.model, device="cpu", compute_type="int8")

    print(f"Transcribing {video.name}…")
    segments, info = model.transcribe(str(video), language=args.language)
    write_outputs(segments, out_dir, video.stem)

    print(f"\nDone.\n  Detected language: {info.language} (p={info.language_probability:.2f})")
    print(f"  Files in {out_dir}/")


if __name__ == "__main__":
    main()
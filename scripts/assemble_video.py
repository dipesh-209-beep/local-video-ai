#!/usr/bin/env python3
"""
assemble_video.py

Combines:
  - a looping background clip (bottom layer)
  - one static diagram image per beat (beat01.png, beat02.png, ...)
  - burned-in captions for the on-screen label + student/teacher lines

Timing comes directly from the actual wav durations recorded in
manifest.json (student_wav / teacher_wav) -- no Whisper transcription
needed, since we already know exactly what was said and for how long.

Usage:
    python3 assemble_video.py \
        --manifest output/shm_video/manifest.json \
        --audio-dir output/shm_video \
        --diagrams-dir output/shm_video/diagrams \
        --background background_loop.mp4 \
        --font /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf \
        --out output/shm_video/final_video.mp4

Requirements: ffmpeg + ffprobe on PATH.
"""

import argparse
import json
import subprocess
from pathlib import Path


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def ffprobe_has_audio(path: Path) -> bool:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return bool(result.stdout.strip())


def escape_drawtext(text: str) -> str:
    """Escape text for ffmpeg's drawtext filter."""
    return (
        text.replace("\\", "\\\\")
            .replace(":", "\\:")
            .replace("'", "\u2019")   # swap apostrophes to avoid quoting issues
            .replace(",", "\\,")
    )


def build_timeline(manifest: dict, audio_dir: Path, gap_sec: float):
    """Compute start/end times for each beat and each line within it."""
    t = 0.0
    timeline = []
    for beat in manifest["beats"]:
        student_wav = audio_dir / beat["student_wav"]
        teacher_wav = audio_dir / beat["teacher_wav"]
        student_dur = ffprobe_duration(student_wav)
        teacher_dur = ffprobe_duration(teacher_wav)

        beat_start = t
        student_start, student_end = t, t + student_dur
        t = student_end + gap_sec
        teacher_start, teacher_end = t, t + teacher_dur
        t = teacher_end + gap_sec
        beat_end = t

        timeline.append({
            "beat_number": beat["beat_number"],
            "on_screen_caption": beat["on_screen_caption"],
            "student_line": beat["student_line"],
            "teacher_line": beat["teacher_line"],
            "beat_start": beat_start,
            "beat_end": beat_end,
            "student_start": student_start,
            "student_end": student_end,
            "teacher_start": teacher_start,
            "teacher_end": teacher_end,
        })
    return timeline, t  # t = total duration


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--audio-dir", required=True, help="dir manifest wav paths are relative to")
    ap.add_argument("--diagrams-dir", required=True, help="dir containing beat01.png, beat02.png, ...")
    ap.add_argument("--background", required=True, help="loopable background video")
    ap.add_argument("--font", required=True, help="path to a bold sans-serif .ttf")
    ap.add_argument("--out", required=True)
    ap.add_argument("--gap-sec", type=float, default=0.35,
                     help="must match SILENCE_BETWEEN_LINES_SEC used in generate_lesson_audio.py")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    audio_dir = Path(args.audio_dir)
    diagrams_dir = Path(args.diagrams_dir)
    font = args.font

    timeline, total_dur = build_timeline(manifest, audio_dir, args.gap_sec)
    bg_has_audio = ffprobe_has_audio(Path(args.background))

    W, H = args.width, args.height

    # ---- Build ffmpeg inputs ----
    inputs = [
        "-stream_loop", "-1", "-i", args.background,          # 0: bg video (looped)
        "-i", str(audio_dir / "final_narration.wav"),          # 1: full narration audio
    ]
    for beat in timeline:
        img = diagrams_dir / f"beat{beat['beat_number']:02d}.png"
        inputs += ["-loop", "1", "-i", str(img)]               # 2..N: diagram stills

    # ---- Build filter graph ----
    filters = []
    filters.append(
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},trim=duration={total_dur:.3f},setpts=PTS-STARTPTS[bg]"
    )

    prev = "bg"
    for i, beat in enumerate(timeline):
        img_input = i + 2  # input index for this beat's diagram
        node = f"ov{i}"
        start, end = beat["beat_start"], beat["beat_end"]
        filters.append(
            f"[{prev}][{img_input}:v]overlay=(W-w)/2:(H-h)/2:"
            f"enable='between(t,{start:.3f},{end:.3f})'[{node}]"
        )
        prev = node

    # ---- Captions: top on-screen label + lower-middle dialogue lines ----
    for beat in timeline:
        top_text = escape_drawtext(beat["on_screen_caption"].upper())
        node = f"cap_top{beat['beat_number']}"
        filters.append(
            f"[{prev}]drawtext=fontfile='{font}':text='{top_text}':"
            f"fontsize=54:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=20:"
            f"x=(w-text_w)/2:y=120:"
            f"enable='between(t,{beat['beat_start']:.3f},{beat['beat_end']:.3f})'[{node}]"
        )
        prev = node

        for role, start_key, end_key in (("student", "student_start", "student_end"),
                                          ("teacher", "teacher_start", "teacher_end")):
            text = escape_drawtext(beat[f"{role}_line"].upper())
            node = f"cap_{role}{beat['beat_number']}"
            filters.append(
                f"[{prev}]drawtext=fontfile='{font}':text='{text}':"
                f"fontsize=46:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=16:"
                f"x=(w-text_w)/2:y=h*0.62:line_spacing=6:"
                f"enable='between(t,{beat[start_key]:.3f},{beat[end_key]:.3f})'[{node}]"
            )
            prev = node

    filter_complex = ";\n".join(filters)
    if bg_has_audio:
        filter_complex += (
            ";[1:a]volume=1.0[narr];"
            "[0:a]volume=0.3[bga];"
            "[narr][bga]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        )
    else:
        filter_complex += ";[1:a]anull[aout]"

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{prev}]",
        "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        "-t", f"{total_dur:.3f}",
        "-fflags", "+genpts",
        args.out,
    ]

    print("Running ffmpeg (this can take a while with many overlay/drawtext stages)...")
    subprocess.run(cmd, check=True)
    print(f"\nDone: {args.out}")


if __name__ == "__main__":
    main()

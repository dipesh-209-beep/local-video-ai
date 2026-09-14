#!/usr/bin/env python3
"""
generate_lesson_audio.py

Turns a STUDENT/TEACHER beat-script (JSON, as produced by your local CLI AI)
into per-line narration audio using your local-video-ai repo's tts.py,
then stitches everything into one final narration track plus a manifest
you can use to time captions and screenshots in the video-assembly step.

Usage:
    python3 generate_lesson_audio.py script.json output_dir/

Assumes it's run from inside your local-video-ai repo (so tts.py and
config/ under scripts/ and config/ are found from the repo root).

Voice setup:
    Set two Piper voice models below (STUDENT_MODEL / TEACHER_MODEL).
    Both must already be downloaded into models/piper/ per your repo's README.
    If you only have one voice installed, set both to the same model --
    the script still works, you'll just lose the two-voice effect until
    you download a second one.
"""

import json
import subprocess
import sys
from pathlib import Path

# ---- Config: adjust to your setup -----------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]  # repo root (local-video-ai/)
SCRIPTS_DIR = REPO_ROOT / "scripts"
TTS_SCRIPT = SCRIPTS_DIR / "tts.py"
STUDENT_MODEL = "en_US-amy-medium"      # example lighter/higher voice
TEACHER_MODEL = "en_US-ryan-medium"     # example lower/authoritative voice
SILENCE_BETWEEN_LINES_SEC = 0.35        # small gap so lines don't run together
# -----------------------------------------------------------------------------


def run_tts(text: str, out_wav: Path, piper_model: str):
    """Write text to a temp file and call the repo's tts.py with a
    per-call --model override."""
    tmp_txt = out_wav.with_suffix(".txt")
    tmp_txt.write_text(text.strip() + "\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(TTS_SCRIPT), str(tmp_txt), str(out_wav), "--model", piper_model],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"tts.py failed for '{text}' (model={piper_model}):\n{result.stderr}"
        )
    tmp_txt.unlink(missing_ok=True)


def make_silence(out_wav: Path, seconds: float, reference_wav: Path):
    """Generate a short silence clip matching the sample rate of an
    existing wav, using ffmpeg."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate", "-of",
         "default=noprint_wrappers=1:nokey=1", str(reference_wav)],
        capture_output=True, text=True,
    )
    sample_rate = probe.stdout.strip() or "22050"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i",
         f"anullsrc=r={sample_rate}:cl=mono", "-t", str(seconds), str(out_wav)],
        capture_output=True, text=True, check=True,
    )


def concat_wavs(wav_list, out_wav: Path):
    """Concatenate a list of wav paths into one file via ffmpeg concat demuxer."""
    list_file = out_wav.parent / "concat_list.txt"
    with open(list_file, "w") as f:
        for w in wav_list:
            f.write(f"file '{w.resolve()}'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
         "-c", "copy", str(out_wav)],
        capture_output=True, text=True, check=True,
    )
    list_file.unlink()


def main(script_path: str, out_dir: str):
    data = json.loads(Path(script_path).read_text())
    out_dir = Path(out_dir)
    lines_dir = out_dir / "lines"
    lines_dir.mkdir(parents=True, exist_ok=True)

    manifest = {"topic": data["topic"], "beats": []}
    all_wavs = []

    for beat in data["beats"]:
        n = beat["beat_number"]

        student_wav = lines_dir / f"beat{n:02d}_student.wav"
        teacher_wav = lines_dir / f"beat{n:02d}_teacher.wav"
        gap_wav = lines_dir / f"beat{n:02d}_gap.wav"

        print(f"[beat {n}] generating student line...")
        run_tts(beat["student_line"], student_wav, STUDENT_MODEL)

        print(f"[beat {n}] generating teacher line...")
        run_tts(beat["teacher_line"], teacher_wav, TEACHER_MODEL)

        make_silence(gap_wav, SILENCE_BETWEEN_LINES_SEC, student_wav)

        manifest["beats"].append({
            "beat_number": n,
            "on_screen_caption": beat["on_screen_caption"],
            "student_line": beat["student_line"],
            "teacher_line": beat["teacher_line"],
            "student_wav": str(student_wav.relative_to(out_dir)),
            "teacher_wav": str(teacher_wav.relative_to(out_dir)),
        })

        all_wavs += [student_wav, gap_wav, teacher_wav, gap_wav]

    final_wav = out_dir / "final_narration.wav"
    print("Stitching final narration track...")
    concat_wavs(all_wavs, final_wav)

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"\nDone.\n  Narration: {final_wav}\n  Manifest:  {manifest_path}")
    print("\nNext step: run Whisper on the final narration to get word-timed captions, e.g.:")
    print(f"  whisper {final_wav} --output_dir {out_dir}/output --model base --language en --output_format all")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 generate_lesson_audio.py script.json output_dir/")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])

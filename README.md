# Local Video AI

A fully local pipeline for making short-form AI videos — workflow copied from the "Peter Brain Riot"-style reaction skits: a STUDENT/TEACHER beat script becomes a finished 1080×1920 vertical video with procedural diagrams, two-voice Piper narration, and burned-in captions over a looping background. No cloud APIs — everything runs on your machine.

Also includes a transcription (faster-whisper) and text-to-speech (Piper) CLI behind a single entry point.

## Features

- **One-command CLI**: `main.py` chains transcription (faster-whisper) + TTS (Piper), with batch mode
- **One-command video pipeline**: `make_video.py` → finished `.mp4`
- **Dual-voice narration**: student + teacher Piper voices, one wav per line
- **Procedural beat diagrams**: `beat01.png … beatNN.png` generated from the script
- **FFmpeg assembly**: diagram sequence + captions + background loop + audio mix
- **Fast CPU transcription**: faster-whisper (CTranslate2/int8) → `.json` / `.srt` / `.vtt` / `.tsv` / `.txt`
- **Environment-based config** (see `config/app.env`)

## Project structure

```
local-video-ai/
├── main.py                    # CLI entry point (transcribe + TTS + batch)
├── setup.sh                   # one-command env setup (venv/ffmpeg/models/config)
├── assets/                    # static media used by the pipeline
│   ├── bg/                    #   background loop videos (1080x1920) — drop any *.mp4 here
│   ├── fonts/                 #   custom fonts (optional, .ttf/.otf)
│   └── references/            #   style-reference / sample videos (pgsg.mp4 etc.)
├── config/                    # environment config (unified: PIPER_* + WHISPER_*)
│   ├── app.env                #   your settings (gitignored)
│   └── app.env.example        #   template / documented defaults
├── content/                   # TTS test text (tts_test.txt)
├── input/                     # one subfolder per project: script + generated content
│   └── shm/                   #   SHM project
│       ├── script.json        #     beat script (source)
│       ├── manifest.json      #     generated beat -> wav timing map
│       ├── final_narration.wav#     generated narration track
│       ├── lines/             #     generated per-line student/teacher/gap wavs
│       └── diagrams/          #     generated beat01.png .. beatNN.png
├── models/                    # model weights (gitignored)
│   ├── piper/                 #   Piper TTS voices (*.onnx)
│   └── whisper/               #   faster-whisper models (auto-downloaded)
├── output/                    # final produced videos + transcripts (gitignored)
│   ├── shm_final_video.mp4    #   one finished render per project
│   └── <video-name>/          #   transcripts: {<video-name>.json,.srt,.vtt,.tsv,.txt}
├── scripts/                   # pipeline code
│   ├── config.py              #   shared config loader (config/app.env)
│   ├── tts.py                 #   Piper TTS wrapper (CLI, --model override)
│   ├── transcribe.py          #   faster-whisper -> txt/srt/vtt/tsv/json
│   ├── generate_lesson_audio.py # beat script JSON -> per-line wavs + manifest
│   ├── make_diagrams.py       #   beat script JSON -> beatNN.png diagrams
│   ├── assemble_video.py      #   diagrams + narration + captions -> final video
│   └── make_video.py          #   one-command pipeline that runs the three above
└── requirements.txt           # pip dependencies (pinned)
```

## Requirements

Run `./setup.sh` (creates venv, installs pinned deps, checks ffmpeg, copies config, downloads Piper voices).

## Configuration

All settings live in `config/app.env` (see `config/app.env.example`):

| Variable               | Description                              | Example              |
|------------------------|------------------------------------------|----------------------|
| `PIPER_MODEL`          | Default Piper voice                      | `en_US-ryan-medium`  |
| `PIPER_DATA_DIR`       | Dir for `.onnx` voices (relative ok)     | `models/piper`       |
| `STUDENT_MODEL`        | Beat-script student voice                | `en_US-amy-medium`   |
| `TEACHER_MODEL`        | Beat-script teacher voice                | `en_US-ryan-medium`  |
| `WHISPER_MODEL`        | faster-whisper model size                | `base`               |
| `WHISPER_LANGUAGE`     | Transcription language code              | `en`                 |
| `WHISPER_OUTPUT_FORMAT`| Output set (kept for compatibility)      | `all`                |
| `WHISPER_BATCH`        | Reserved for future batch flags          | `false`              |

## Usage

### 1. Full video from a beat script (one command)

Write a beat script like `input/shm/script.json` (topic + beats, each with `beat_number`, `on_screen_caption`, `student_line`, `teacher_line`), then run:

```bash
python3 scripts/make_video.py input/shm/script.json \
    --background assets/bg/background_loop.mp4 \
    --font /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
```

Generated content lands next to the script and the final video in `output/`:

```
input/shm/
├── script.json            # your beat script (source)
├── final_narration.wav    # concatenated narration track
├── manifest.json          # beat -> wav timing map
├── lines/                 # per-line student/teacher/gap wavs
└── diagrams/              # beat01.png .. beatNN.png

output/
└── shm_final_video.mp4    # the finished vertical video
```

Overrides: `--work-dir` relocates intermediates, `--output <path>` sets the final video path.

Voices are set in `scripts/generate_lesson_audio.py` (`STUDENT_MODEL` / `TEACHER_MODEL` at the top).

### 2. Step by step

```bash
# narration (into the script's project folder)
python3 scripts/generate_lesson_audio.py input/shm/script.json input/shm/

# diagrams
python3 scripts/make_diagrams.py input/shm/script.json input/shm/diagrams/

# assembly
python3 scripts/assemble_video.py --manifest input/shm/manifest.json \
    --audio-dir input/shm \
    --diagrams-dir input/shm/diagrams \
    --background assets/bg/background_loop.mp4 \
    --font /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf \
    --out output/shm_final_video.mp4
```

### 3. Transcription (+ TTS) via the CLI entry point

Transcribe one file (outputs go to `output/<video-name>/`):

```bash
python3 main.py input/video.mp4
```

Batch-transcribe every media file under `input/` into per-video subfolders
`output/<video-name>/`:

```bash
python3 main.py --batch
```

Transcribe a file *and* synthesize a Piper voiceover:

```bash
python3 main.py input/video.mp4 --tts content/tts_test.txt
```

Direct faster-whisper call (five formats: txt/srt/vtt/tsv/json):

```bash
python3 scripts/transcribe.py input/video.mp4 --output_dir output/video-name
```

### 4. Single text-to-speech voiceover

```bash
python3 scripts/tts.py content/tts_test.txt output.wav --model en_US-ryan-medium
```

`tts.py` loads `config/app.env` automatically; `--model` overrides it for a single call.

### 5. Quick render test

```bash
ffmpeg -f lavfi -i "testsrc2=size=1080x1920:rate=30:duration=10" \
       -f lavfi -i "sine=frequency=440:duration=10" \
       -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest output/tests/test_10s.mp4
```

### 6. Environment setup

```bash
./setup.sh
```

## Notes

- One project = one subfolder inside `input/` (script + its generated content). The final video lands in `output/` as `<project>_final_video.mp4`.
- Background loops go in `assets/bg/` (1080x1920, loopable). Every `*.mp4` there is picked as a video background.
- Styled reference videos live in `assets/references/`.
- `.venv/`, `models/`, `output/`, `*.mp4`, `*.wav`, `*.onnx`, `*.log`, `input/*/diagrams/`, and `config/*.env` are ignored via `.gitignore` — model weights, env files, generated intermediates, and finished media stay local.
- Caption timing comes from the actual wav durations in `manifest.json` — no Whisper pass needed on the narration, since the script already knows exactly what was said.
- The gap between lines (0.35s) is defined once in `scripts/generate_lesson_audio.py` and passed to the assembler automatically by `make_video.py`.
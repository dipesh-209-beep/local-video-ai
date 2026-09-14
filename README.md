# Local Video AI

A fully local pipeline for processing videos: speech-to-text transcription with OpenAI Whisper (JSON / SRT / VTT / TSV output) and text-to-speech voiceovers with Piper. No cloud APIs — everything runs on your machine.

## Features

- **Local transcription** of videos into timestamped subtitles and transcripts
- **Multiple output formats**: `.json`, `.srt`, `.vtt`, `.tsv`, `.txt`
- **Local text-to-speech** voiceovers using Piper neural voices
- **Environment-based config** (see `config/tts.env`)

## Project structure

```
.
├── config/           # Environment config (PIPER_MODEL, PIPER_DATA_DIR)
├── input/            # Source videos / audio to transcribe
├── models/piper/     # Downloadable TTS voices (*.onnx)
├── output/           # Transcriptions: json/srt/vtt/tsv/txt
├── tts.py            # Piper TTS wrapper
├── test_script.txt   # Sample narration script
└── .venv/            # Python virtual environment (not committed)
```

## Requirements

- Python 3.10+ and a virtual environment with your transcription and TTS packages installed (e.g. `openai-whisper`, `pip install piper-tts`)
- ffmpeg (`sudo apt install ffmpeg`)
- Piper voice models in `models/piper/` (e.g. `en_US-ryan-medium.onnx`)

## Usage

### 1. Text-to-speech voiceover

```bash
python3 tts.py test_script.txt output.wav
```

`tts.py` loads `config/tts.env` automatically, so you can set the model and data dir without editing the script:

```
PIPER_MODEL=en_US-ryan-medium
PIPER_DATA_DIR=/home/<user>/local-video-ai/models/piper   # defaults to models/piper
```

### 2. Transcription

Put a video in `input/`, then transcribe it with Whisper so the caption/timestamp files land in `output/`:

```bash
whisper input/video.mp4 --output_dir output --model base --language en \
  --output_format all
```

Generated files (`newtons_laws_short.{json,srt,vtt,tsv,txt}`) can be burned into video or used as subtitles.

## Configuration

| Variable         | Description                              | Example                     |
|------------------|------------------------------------------|-----------------------------|
| `PIPER_MODEL`    | Piper voice model name                   | `en_US-ryan-medium`         |
| `PIPER_DATA_DIR` | Directory containing the `.onnx` voices  | `models/piper`              |

## Notes

- `.venv/`, `models/`, `output/`, `*.mp4`, and `config/*.env` are ignored via `.gitignore` — model weights and env files stay local.
- Sample output for `newtons_laws_short.mp4` is in `output/`.
#!/usr/bin/env bash
#
# setup.sh — one-command environment setup for local-video-ai.
#
# Creates the venv, installs pinned deps, checks ffmpeg, creates config/app.env
# from the example, and downloads the two Piper voices used by the pipeline.
#
# Usage:  ./setup.sh
#
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US"
VOICES=(en_US-amy-medium:amy/medium:en_US-amy-medium
        en_US-ryan-medium:ryan/medium:en_US-ryan-medium)

echo "==> Creating venv (.venv)…"
if [ ! -d .venv ]; then
    "$PY" -m venv .venv
fi
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet

echo "==> Checking ffmpeg…"
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "ffmpeg not found."
    if command -v sudo >/dev/null 2>&1; then
        sudo apt-get install -y ffmpeg
    else
        echo "ERROR: install ffmpeg (e.g. 'sudo apt install ffmpeg') and re-run." >&2
        exit 1
    fi
fi
ffmpeg -version | head -1

echo "==> Creating config/app.env if missing…"
mkdir -p config
if [ ! -f config/app.env ]; then
    cp config/app.env.example config/app.env
    echo "  created config/app.env (defaults) — edit to taste"
else
    echo "  config/app.env already exists — leaving as-is"
fi

echo "==> Downloading Piper voices…"
mkdir -p models/piper
for entry in "${VOICES[@]}"; do
    name="${entry%%:*}"
    path="${entry#*:}"; path="${path%%:*}"   # amy/medium
    file="${entry##*:}"
    onnx="models/piper/${name}.onnx"
    if [ -f "$onnx" ]; then
        echo "  $name already present — skipping"
        continue
    fi
    echo "  downloading ${name}…"
    curl -L --fail --progress-bar \
         "${BASE_URL}/${path}/${file}.onnx" -o "$onnx"
    curl -L --fail --progress-bar \
         "${BASE_URL}/${path}/${file}.onnx.json" -o "${onnx}.json"
done
ls -1 models/piper/ | grep -c '\.onnx$' | xargs -I{} echo "  {} Piper model(s) ready."

echo ""
echo "Setup complete."
echo "  Activate:   source .venv/bin/activate"
echo "  Transcribe: python3 main.py --batch"
echo "  Make video: python3 scripts/make_video.py input/shm/script.json \\"
echo "                  --background assets/bg/background_loop.mp4 \\"
echo "                  --font /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
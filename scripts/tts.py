import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"'))


load_env(PROJECT_ROOT / "config/tts.env")

MODEL = os.environ.get("PIPER_MODEL", "en_US-ryan-medium")
data_dir = os.environ.get("PIPER_DATA_DIR")
DATA_DIR = Path(data_dir) if data_dir else PROJECT_ROOT / "models" / "piper"

parser = argparse.ArgumentParser(description="Piper text-to-speech wrapper")
parser.add_argument("text_file", help="input text file")
parser.add_argument("output", nargs="?", default="output.wav", help="output wav path")
parser.add_argument("--model", default=MODEL, help="Piper voice model (overrides config/tts.env)")
args = parser.parse_args()

cmd = [
    "python3", "-m", "piper",
    "--data-dir", str(DATA_DIR),
    "-m", args.model,
    "-i", str(args.text_file),
    "-f", str(args.output),
]

subprocess.run(cmd, check=True)

print(f"Created: {args.output}")
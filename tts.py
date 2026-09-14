import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


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

if len(sys.argv) < 2:
    print("Usage: python3 tts.py script.txt [output.wav]")
    sys.exit(1)

text_file = Path(sys.argv[1])
output = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output.wav")

cmd = [
    "python3", "-m", "piper",
    "--data-dir", str(DATA_DIR),
    "-m", MODEL,
    "-i", str(text_file),
    "-f", str(output),
]

subprocess.run(cmd, check=True)

print(f"Created: {output}")
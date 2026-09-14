import sys
import subprocess
from pathlib import Path

MODEL = "en_US-ryan-medium"
DATA_DIR = Path.home() / "local-video-ai/models/piper"

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

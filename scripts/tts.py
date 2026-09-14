import argparse
import subprocess
import sys
from pathlib import Path

from config import config_path, load_config

cfg = load_config()
DATA_DIR = Path(cfg["PIPER_DATA_DIR"])


def die(msg: str) -> None:
    print(f"tts.py: {msg}", file=sys.stderr)
    sys.exit(1)


def require_piper():
    try:
        subprocess.run(
            [sys.executable, "-m", "piper", "--help"],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError:
        die("piper is not installed — run '.venv/bin/pip install -r requirements.txt'")
    except subprocess.TimeoutExpired:
        pass


def main():
    parser = argparse.ArgumentParser(description="Piper text-to-speech wrapper")
    parser.add_argument("text_file", help="input text file")
    parser.add_argument("output", nargs="?", default="output.wav", help="output wav path")
    parser.add_argument("--model", default=cfg["PIPER_MODEL"],
                        help="Piper voice model (overrides config/app.env)")
    args = parser.parse_args()

    if not config_path().exists():
        print("warning: config/app.env not found, using defaults (see config/app.env.example)",
              file=sys.stderr)

    text_file = Path(args.text_file)
    if not text_file.exists():
        die(f"text file not found: {text_file}")

    model = Path(args.model) if Path(args.model).suffix else None
    model_file = model or (DATA_DIR / f"{args.model}.onnx")
    if not model_file.exists():
        die(f"voice model not found: {model_file} — run ./setup.sh to download it")

    require_piper()

    cmd = [
        sys.executable, "-m", "piper",
        "--data-dir", str(DATA_DIR),
        "-m", args.model,
        "-i", str(text_file),
        "-f", str(args.output),
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        die(f"piper failed (exit {e.returncode}): {e.stderr.strip() if e.stderr else str(e)}")
    except FileNotFoundError:
        die("piper is not installed — run '.venv/bin/pip install -r requirements.txt'")

    print(f"Created: {args.output}")


if __name__ == "__main__":
    main()
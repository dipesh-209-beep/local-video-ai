import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULTS = {
    "PIPER_MODEL": "en_US-ryan-medium",
    "PIPER_DATA_DIR": "models/piper",
    "STUDENT_MODEL": "en_US-amy-medium",
    "TEACHER_MODEL": "en_US-ryan-medium",
    "WHISPER_MODEL": "base",
    "WHISPER_LANGUAGE": "en",
    "WHISPER_OUTPUT_FORMAT": "all",
    "WHISPER_BATCH": "false",
}


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"'))


def load_config() -> dict:
    """Load config/app.env (if present) merged over defaults.

    Returns a dict of resolved settings. PIPER_DATA_DIR is resolved to an
    absolute path relative to the repo root unless it already is one.
    """
    load_env(ROOT / "config" / "app.env")
    cfg = {key: os.environ.get(key, default) for key, default in DEFAULTS.items()}
    data_dir = Path(cfg["PIPER_DATA_DIR"])
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir
    cfg["PIPER_DATA_DIR"] = str(data_dir)
    return cfg


def config_path() -> Path:
    return ROOT / "config" / "app.env"
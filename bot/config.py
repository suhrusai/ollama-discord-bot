import os
from pathlib import Path
from typing import Any

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"


def _load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}

    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _get_raw(key: str, default: Any = None) -> Any:
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value

    return _CONFIG.get(key, default)


def _normalize_int(value: Any, default: int) -> int:
    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


_CONFIG = _load_config()

DISCORD_TOKEN = _get_raw("DISCORD_TOKEN")
OLLAMA_CHAT = _get_raw("OLLAMA_CHAT", "http://localhost:11434/api/chat")
OLLAMA_TAGS = _get_raw("OLLAMA_TAGS", "http://localhost:11434/api/tags")
DEFAULT_MODEL = _get_raw("DEFAULT_MODEL", "qwen3.5:latest")
LOG_LEVEL = str(_get_raw("LOG_LEVEL", "INFO")).upper()
UPLOAD_ROOT = _get_raw("UPLOAD_ROOT", "uploads")
OLLAMA_PARALLELISM = _normalize_int(_get_raw("OLLAMA_PARALLELISM", 1), 1)

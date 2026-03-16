import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", verbose=False)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_CHAT = os.getenv("OLLAMA_CHAT", "http://localhost:11434/api/chat")
OLLAMA_TAGS = os.getenv("OLLAMA_TAGS", "http://localhost:11434/api/tags")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen3.5:latest")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", "uploads")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")

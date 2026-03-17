from __future__ import annotations

import base64
import zlib

from bot.config import DEFAULT_MODEL

HISTORY_LIMIT = 8

chat_history: dict[str, list[dict[str, object]]] = {}
user_models: dict[str, str] = {}


def _compress_text(text: str) -> str:
    return base64.b64encode(zlib.compress(text.encode("utf-8"), level=6)).decode("utf-8")


def _decompress_text(value: str) -> str:
    return zlib.decompress(base64.b64decode(value.encode("utf-8"))).decode("utf-8")


def _decode_entry(entry: dict[str, object]) -> dict[str, object]:
    decoded = entry.copy()
    if "content" in decoded:
        decoded["content"] = _decompress_text(decoded["content"])  # type: ignore[arg-type]
    return decoded


def append_history(user_id: str, role: str, content: str | None, images: list[str] | None = None):
    entry: dict[str, object] = {"role": role}
    if content:
        entry["content"] = _compress_text(content)
    if images:
        entry["images"] = images

    history = chat_history.setdefault(user_id, [])
    history.append(entry)
    chat_history[user_id] = history[-HISTORY_LIMIT:]


def clear_history(user_id: str):
    chat_history[user_id] = []


def get_decoded_history(user_id: str) -> list[dict[str, object]]:
    return [_decode_entry(entry) for entry in chat_history.get(user_id, [])]


def get_user_model(user_id: str):
    return user_models.get(user_id, DEFAULT_MODEL)


def set_user_model(user_id: str, model: str):
    user_models[user_id] = model


def reset_user_state(user_id: str):
    user_models.pop(user_id, None)
    chat_history.pop(user_id, None)

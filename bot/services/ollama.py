import asyncio
import base64
import logging
from pathlib import Path

import aiohttp

from bot.config import (
    DEFAULT_MODEL,
    OLLAMA_CHAT,
    OLLAMA_PARALLELISM,
    OLLAMA_RESPONSE_TIMEOUT,
    OLLAMA_SUMMARY_TIMEOUT,
    OLLAMA_TAGS,
)
from bot.files.heic_converter import convert_heic_to_jpg
from bot.prompts import SYSTEM_PROMPT
from bot.state import (
    HISTORY_LIMIT,
    append_history,
    clear_history,
    get_decoded_history,
    get_user_model,
)

logger = logging.getLogger("discord-ai.services.ollama")
ollama_semaphore = asyncio.Semaphore(OLLAMA_PARALLELISM)

SUMMARY_SYSTEM_PROMPT = (
    "You are a context compression assistant. Summarize the following "
    "conversation into a short paragraph (<= 200 words) while preserving "
    "the user intent and any outstanding action items."
)


async def get_models():
    timeout = aiohttp.ClientTimeout(total=3000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(OLLAMA_TAGS) as resp:
            data = await resp.json()
            return [model["name"] for model in data.get("models", [])]

async def ask_ollama(user_id, prompt, files=None):
    await _maybe_compress_history(user_id)
    history = get_decoded_history(user_id)
    messages = [SYSTEM_PROMPT] + history
    file_context = ""
    images = []

    image_extensions = {"png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"}

    if files:
        logger.info("%s uploaded %s file(s)", user_id, len(files))

        for file_path in files:
            try:
                filename = Path(file_path).name
                ext = filename.split(".")[-1].lower()
                dir_path = Path(file_path).parent
                stem = Path(file_path).stem

                if ext == "heic":
                    try:
                        new_file_name = f"{stem}.jpg"
                        new_file_path = dir_path / new_file_name
                        logger.info("Converting %s to %s", filename, new_file_path)
                        convert_heic_to_jpg(file_path, new_file_path)
                        file_path = str(new_file_path)
                        logger.info("Converted %s to %s", filename, new_file_path)
                    except Exception as exc:
                        logger.error("Failed to convert HEIC: %s", exc)

                    logger.info("Encoding image: %s", filename)

                    encoded = await asyncio.to_thread(
                        lambda: base64.b64encode(open(file_path, "rb").read()).decode()
                    )

                    images.append(encoded)
                    continue
                elif ext in image_extensions:
                    logger.info("Encoding image: %s", filename)

                    encoded = await asyncio.to_thread(
                        lambda: base64.b64encode(Path(file_path).read_bytes()).decode()
                    )

                    images.append(encoded)
                elif ext not in {"exe", "dll", "msi"}:
                    def read_file():
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                            return fh.read(4000)

                    content = await asyncio.to_thread(read_file)
                    file_context += f"\n\nFile: {filename}\n```\n{content}\n```"
                else:
                    file_context += f"\n\nUser uploaded file: {filename}"
            except Exception as exc:
                logger.error("File read error: %s", exc)

    final_prompt = prompt + file_context

    user_message = {
        "role": "user",
        "content": final_prompt
    }

    if images:
        user_message["images"] = images

    messages.append(user_message)

    payload = {
        "model": get_user_model(user_id),
        "messages": messages,
        "stream": False
    }

    logger.info("Sending prompt to Ollama from user %s", user_id)

    timeout = aiohttp.ClientTimeout(total=OLLAMA_RESPONSE_TIMEOUT)

    try:
        data = await _send_payload(payload, timeout=timeout)
        content = _extract_content(data)
    except asyncio.TimeoutError:
        logger.error("Ollama request timed out")
        return '{"messages":[{"content":"⚠️ Ollama took too long to respond."}]}'

    append_history(user_id, "user", final_prompt, images if images else None)
    append_history(user_id, "assistant", content, None)

    return content


async def _maybe_compress_history(user_id: str):
    history = get_decoded_history(user_id)
    if len(history) < HISTORY_LIMIT:
        return

    summary = await _summarize_history(history)
    if summary:
        clear_history(user_id)
        append_history(user_id, "system", summary)
        logger.info("Context compressed for %s: %s", user_id, summary)


async def _summarize_history(history: list[dict[str, object]]) -> str | None:
    filtered = [entry for entry in history if entry.get("content")]
    if not filtered:
        return None

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "system", "content": SUMMARY_SYSTEM_PROMPT}] + filtered,
        "stream": False
    }

    try:
        data = await _send_payload(payload, timeout=aiohttp.ClientTimeout(total=OLLAMA_SUMMARY_TIMEOUT))
    except asyncio.TimeoutError:
        logger.warning("Context summarization timed out; keeping existing history.")
        return None

    summary = _extract_content(data)
    logger.info("Summarized history: %s", summary)
    return summary


async def _send_payload(payload: dict[str, object], timeout: aiohttp.ClientTimeout):
    async with ollama_semaphore:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(OLLAMA_CHAT, json=payload) as resp:
                data = await resp.json()
                logger.info("Ollama raw response: %s", data)
                return data


def _extract_content(data: dict[str, object]) -> str:
    if "message" in data and "content" in data["message"]:
        return data["message"]["content"]
    if "response" in data:
        return data["response"]
    if "error" in data:
        return f"⚠️ Ollama error: {data['error']}"
    return "⚠️ Unknown Ollama response format."

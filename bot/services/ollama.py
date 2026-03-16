import asyncio
import base64
import logging
from pathlib import Path

import aiohttp

from bot.config import OLLAMA_CHAT, OLLAMA_TAGS
from bot.files.heic_converter import convert_heic_to_jpg
from bot.prompts import SYSTEM_PROMPT
from bot.state import chat_history, get_user_model

logger = logging.getLogger("discord-ai.services.ollama")

async def get_models():
    timeout = aiohttp.ClientTimeout(total=3000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(OLLAMA_TAGS) as resp:
            data = await resp.json()
            return [model["name"] for model in data.get("models", [])]

async def ask_ollama(user_id, prompt, files=None):
    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id] = chat_history[user_id][-8:]

    messages = [SYSTEM_PROMPT] + chat_history[user_id]
    file_context = ""
    images = []

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

    timeout = aiohttp.ClientTimeout(total=3600)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(OLLAMA_CHAT, json=payload) as resp:
                data = await resp.json()
                logger.info("Ollama raw response: %s", data)

                if "message" in data and "content" in data["message"]:
                    content = data["message"]["content"]
                elif "response" in data:
                    content = data["response"]
                elif "error" in data:
                    content = f"⚠️ Ollama error: {data['error']}"
                else:
                    content = "⚠️ Unknown Ollama response format."
    except asyncio.TimeoutError:
        logger.error("Ollama request timed out")
        return '{"messages":[{"content":"⚠️ Ollama took too long to respond."}]}'

    chat_history[user_id].append({
        "role": "user",
        "content": final_prompt,
        "images": images if images else None
    })

    chat_history[user_id].append({
        "role": "assistant",
        "content": content
    })

    logger.info("Ollama response length: %s characters", len(content))

    return content

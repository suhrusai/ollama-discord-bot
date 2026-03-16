import asyncio
from collections import deque

import discord

from bot.client import client
from bot.logger import logger
from bot.messaging import send_ai_json
from bot.services.attachments import save_user_attachments
from bot.services.ollama import ask_ollama

queue_lock = asyncio.Lock()
queue = deque()


async def enter_queue():
    event = asyncio.Event()
    async with queue_lock:
        queue.append(event)
        position = len(queue)
        if position == 1:
            event.set()
    return position, event


async def leave_queue(event: asyncio.Event):
    async with queue_lock:
        if queue and queue[0] is event:
            queue.popleft()
            if queue:
                queue[0].set()


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if client.user not in message.mentions:
        return

    user_id = str(message.author.id)
    await message.channel.typing()

    prompt = message.content.replace(f"<@{client.user.id}>", "") \
        .replace(f"<@!{client.user.id}>", "").strip()

    logger.info("Prompt from %s: %s", user_id, prompt)

    position, event = await enter_queue()
    queue_msg = None
    if position > 1:
        queue_msg = await message.channel.send(
            f"Queue #{position}: waiting for the current request before calling Ollama."
        )

    await event.wait()

    try:
        saved_files = await save_user_attachments(user_id, message.attachments)
        response = await ask_ollama(user_id, prompt, saved_files)
        await send_ai_json(message.channel, response, reply_to=message)
    finally:
        if queue_msg:
            try:
                await queue_msg.delete()
            except discord.HTTPException:
                pass

        await leave_queue(event)

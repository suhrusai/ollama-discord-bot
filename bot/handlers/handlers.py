import discord

from bot.client import client, tree
from bot.services.attachments import delete_user_uploads, save_user_attachments
from bot.config import DISCORD_GUILD_ID
from bot.logger import logger
from bot.messaging import send_ai_json
from bot.services.ollama import ask_ollama, get_models
from bot.state import get_user_model, reset_user_state, set_user_model


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

    saved_files = await save_user_attachments(user_id, message.attachments)
    response = await ask_ollama(user_id, prompt, saved_files)

    await send_ai_json(message.channel, response)


@tree.command(name="clear", description="Clear chat memory")
async def clear(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    reset_user_state(user_id)
    delete_user_uploads(user_id)
    await interaction.response.send_message("Conversation cleared")


class ModelDropdown(discord.ui.Select):
    def __init__(self, models, user_id):
        self.user_id = user_id
        options = [discord.SelectOption(label=model) for model in models]
        super().__init__(placeholder="Select model", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_model = self.values[0]
        set_user_model(self.user_id, selected_model)
        await interaction.response.send_message(f"Model switched to {selected_model}")


class ModelView(discord.ui.View):
    def __init__(self, models, user_id):
        super().__init__()
        self.add_item(ModelDropdown(models, user_id))


@tree.command(name="models", description="Select model")
async def models(interaction: discord.Interaction):
    models_list = await get_models()
    view = ModelView(models_list, str(interaction.user.id))
    await interaction.response.send_message("Choose model:", view=view)


@tree.command(name="current", description="Show current model")
async def current(interaction: discord.Interaction):
    await interaction.response.send_message(f"Current model: {get_user_model(str(interaction.user.id))}")


@client.event
async def on_ready():
    await tree.sync()

    if DISCORD_GUILD_ID:
        try:
            guild_target = discord.Object(id=int(DISCORD_GUILD_ID))
            tree.copy_global_to(guild=guild_target)
            await tree.sync(guild=guild_target)
            logger.info("Synced commands for guild %s", DISCORD_GUILD_ID)
        except ValueError:
            logger.warning("Discord guild ID %s is not numeric; skipping guild sync", DISCORD_GUILD_ID)

    logger.info("Logged in as %s", client.user)
    logger.info("Model: %s", get_user_model(str(client.user.id)))

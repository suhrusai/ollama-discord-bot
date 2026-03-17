import discord
from discord import app_commands

from bot.client import client, tree
from bot.config import BIRTHDAY_MCP_BASE_URL
from bot.logger import logger
from bot.services.attachments import delete_user_uploads
from birthday_bot_mcp_server import MCPError, get_current_weather
from bot.services.ollama import get_models
from bot.state import get_user_model, reset_user_state, set_user_model


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


@tree.command(name="weather", description="Fetch current weather from the MCP server")
async def weather(
    interaction: discord.Interaction,
    latitude: app_commands.Range[float, -90.0, 90.0],
    longitude: app_commands.Range[float, -180.0, 180.0],
):
    try:
        weather_data = await get_current_weather(latitude, longitude, base_url=BIRTHDAY_MCP_BASE_URL)
    except MCPError as exc:
        await interaction.response.send_message(str(exc), ephemeral=True)
        return

    embed = discord.Embed(
        title="Current Weather",
        description=f"Locale: {latitude:.4f}, {longitude:.4f}",
        color=0x1D8BFF
    )

    embed.add_field(name="Temperature (°C)", value=f"{weather_data['temperature']:.1f}", inline=True)
    embed.add_field(name="Wind Speed (km/h)", value=f"{weather_data['windspeed']:.1f}", inline=True)
    embed.add_field(name="Wind Direction", value=f"{weather_data['winddirection']:.0f}°", inline=True)
    embed.add_field(name="Weather Code", value=str(weather_data["weathercode"]), inline=True)
    embed.add_field(name="Local Time", value=weather_data["time"], inline=True)
    embed.set_footer(text=f"Timezone: {weather_data['timezone']}")

    await interaction.response.send_message(embed=embed)


@client.event
async def on_ready():
    await tree.sync()

    for guild in client.guilds:
        guild_target = discord.Object(id=guild.id)
        tree.copy_global_to(guild=guild_target)
        await tree.sync(guild=guild_target)
        logger.info("Synced commands for guild %s (%s)", guild.id, guild.name)

    logger.info("Logged in as %s", client.user)
    logger.info("Model: %s", get_user_model(str(client.user.id)))

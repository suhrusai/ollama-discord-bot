import pkgutil

from bot.client import client
from bot.config import DISCORD_TOKEN
from bot.logger import configure_logging, logger
from bot import events

for module in pkgutil.iter_modules(events.__path__):
    __import__(f"bot.events.{module.name}")

def run():
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN must be set in .env before starting the bot.")

    configure_logging()
    logger.info("Starting Discord AI client")
    client.run(DISCORD_TOKEN)

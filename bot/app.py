import pkgutil

from bot.client import client
from bot.config import DISCORD_TOKEN
from bot.logger import configure_logging, logger
from bot import handlers

for module in pkgutil.iter_modules(handlers.__path__):
    __import__(f"bot.handlers.{module.name}")

def run():
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN must be set in .env before starting the bot.")

    configure_logging()
    logger.info("Starting Discord AI client")
    client.run(DISCORD_TOKEN)

import logging

from bot.config import LOG_LEVEL

logger = logging.getLogger("discord-ai")

def configure_logging():
    """Apply linted formatting and level configuration for the bot."""
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )
    logger.setLevel(level)

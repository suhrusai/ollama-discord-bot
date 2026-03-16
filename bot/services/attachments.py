import shutil
import uuid
from pathlib import Path

from bot.config import UPLOAD_ROOT
from bot.logger import logger


async def save_user_attachments(user_id, attachments):
    saved_files = []
    user_folder = Path(UPLOAD_ROOT) / user_id
    user_folder.mkdir(parents=True, exist_ok=True)

    for attachment in attachments:
        stem = Path(attachment.filename).stem
        filename = f"{stem}_{uuid.uuid4()}{Path(attachment.filename).suffix}"
        file_path = user_folder / filename

        logger.info("Saving attachment from %s: %s", user_id, filename)
        await attachment.save(str(file_path))
        saved_files.append(str(file_path))

        if attachment.content_type and attachment.content_type.startswith("image"):
            logger.info("Image uploaded by %s: %s", user_id, filename)

    return saved_files


def delete_user_uploads(user_id):
    target = Path(UPLOAD_ROOT) / user_id
    if not target.exists():
        return

    try:
        shutil.rmtree(target)
        logger.info("Removed upload folder for %s", user_id)
    except Exception as exc:
        logger.error("Failed to delete uploads for %s: %s", user_id, exc)

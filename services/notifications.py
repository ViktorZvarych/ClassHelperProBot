# Надсилання повідомлень адмінам

import logging
from config import settings
from bot.instance import bot

logger = logging.getLogger(__name__)

async def notify_admins(text: str):
    for admin_id in settings.SUPER_ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

async def notify_admins_throttled(redis, user_id, text):
    key = f"start_notify:{user_id}"
    if await redis.exists(key):
        return
    await redis.setex(key, 600, "1")
    await notify_admins(text)
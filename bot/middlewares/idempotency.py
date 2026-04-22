 # Ідемпотентність update та callback
 
 import logging
from aiogram import BaseMiddleware
from aiogram.types import Update, CallbackQuery
from typing import Any, Awaitable, Callable, Dict

logger = logging.getLogger(__name__)

class WebhookIdempotencyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        redis = data.get("redis")
        update_id = event.update_id
        if redis:
            key = f"processed_update:{update_id}"
            if await redis.exists(key):
                logger.debug(f"Duplicate update {update_id}, skipping")
                return
            await redis.setex(key, 86400, "1")
        else:
            logger.warning("Redis unavailable, idempotency check skipped")
        return await handler(event, data)

class CallbackIdempotencyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        redis = data.get("redis")
        if redis:
            key = f"callback_processed:{event.id}"
            if await redis.exists(key):
                await event.answer()
                return
            await redis.setex(key, 60, "1")
        else:
            logger.warning("Redis unavailable, callback idempotency skipped")
        return await handler(event, data)
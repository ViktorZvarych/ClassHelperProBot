# Rate limiting

import logging
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from typing import Any, Awaitable, Callable, Dict

logger = logging.getLogger(__name__)

class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        redis = data.get("redis")
        user_id = None
        if event.message:
            user_id = event.message.from_user.id
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
        else:
            return await handler(event, data)

        if redis:
            key = f"throttle:{user_id}"
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 3)
            if count > 3:
                if event.message:
                    await event.message.answer("🐢 Надто багато запитів. Зачекайте кілька секунд.")
                elif event.callback_query:
                    await event.callback_query.answer("Зачекайте кілька секунд.", show_alert=True)
                return
        else:
            logger.warning("Redis unavailable, throttling skipped")

        return await handler(event, data)
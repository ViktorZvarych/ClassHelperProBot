# Перевірка ролі та реєстрації

import logging
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from typing import Any, Awaitable, Callable, Dict
from db.queries.students import get_student_by_telegram_id
from config import settings

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
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

        data["is_super_admin"] = user_id in settings.super_admin_ids_set

        # Try cache
        student = None
        if redis:
            cache_key = f"student_cache:{user_id}"
            cached = await redis.get(cache_key)
            if cached:
                import json
                student = json.loads(cached)
            else:
                student = await get_student_by_telegram_id(data["db"], user_id)
                if student:
                    await redis.setex(cache_key, 60, json.dumps(dict(student)))
        else:
            student = await get_student_by_telegram_id(data["db"], user_id)

        data["student"] = student
        return await handler(event, data)
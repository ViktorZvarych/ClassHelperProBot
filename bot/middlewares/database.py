from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Any, Awaitable, Callable, Dict

class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        # Тепер беремо db_pool напряму з data
        pool = data["db_pool"]
        async with pool.acquire() as conn:
            data["db"] = conn
            return await handler(event, data)
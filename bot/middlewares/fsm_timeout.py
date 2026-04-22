# Перевірка TTL стану FSM

from aiogram import BaseMiddleware
from aiogram.types import Update, Message
from aiogram.fsm.context import FSMContext
from typing import Any, Awaitable, Callable, Dict

class FsmTimeoutMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        # Not fully implemented; simplified: rely on aiogram's TTL
        # The TTL is set on RedisStorage, so state will be None after timeout.
        return await handler(event, data)
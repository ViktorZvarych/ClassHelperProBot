from aiogram import Dispatcher
from .idempotency import WebhookIdempotencyMiddleware, CallbackIdempotencyMiddleware
from .database import DatabaseMiddleware
from .auth import AuthMiddleware
from .fsm_timeout import FsmTimeoutMiddleware
from .throttling import ThrottlingMiddleware

def setup_middlewares(dp: Dispatcher):
    # Outer first
    dp.update.middleware(WebhookIdempotencyMiddleware())
    dp.update.middleware(DatabaseMiddleware())
    # Inner
    dp.update.middleware(AuthMiddleware())
    dp.update.middleware(FsmTimeoutMiddleware())
    dp.update.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(CallbackIdempotencyMiddleware())
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.types import BotCommand
from redis.asyncio import Redis
import sentry_sdk

from config import settings
from db.pool import create_db_pool, close_db_pool
from bot.instance import bot
from bot.middlewares import setup_middlewares
from bot.handlers import setup_routers
from web.app import create_app
from services.broadcast_queue import broadcast_queue, start_broadcast_workers, stop_broadcast_workers
from services.notifications import notify_admins

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment="production",
    )

async def on_startup(app: web.Application):
    # PostgreSQL
    try:
        app["db_pool"] = await create_db_pool()
        async with app["db_pool"].acquire() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database pool created and verified")
    except Exception as e:
        logger.critical(f"Database connection failed: {e}")
        raise

    # Redis
    try:
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis.ping()
        app["redis"] = redis
        logger.info("Redis connected")
    except Exception as e:
        logger.critical(f"Redis connection failed: {e}")
        raise

    # Telegram Bot
    try:
        await bot.get_chat(settings.GROUP_CHAT_ID)
        logger.info("Group chat verified")
    except Exception as e:
        logger.critical(f"Group chat {settings.GROUP_CHAT_ID} is invalid: {e}")
        raise

    # FSM Storage
    storage = RedisStorage.from_url(
        url=settings.REDIS_URL,
        key_builder=DefaultKeyBuilder(with_destiny=True),
        state_ttl=300,
        data_ttl=300,
    )

    # Створюємо Dispatcher зі storage
    dp = Dispatcher(storage=storage)
    dp["db_pool"] = app["db_pool"]
    dp["redis"] = redis
    app["dp"] = dp

    # Middlewares & Routers
    setup_middlewares(dp)
    setup_routers(dp)

    # Webhook setup
    await bot.delete_webhook(drop_pending_updates=True)
    webhook_url = f"{settings.RENDER_EXTERNAL_URL}/webhook"
    await bot.set_webhook(webhook_url, secret_token=settings.WEBHOOK_SECRET)
    logger.info(f"Webhook set to {webhook_url}")

    # Set bot commands
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустити бота / головне меню"),
        BotCommand(command="myid", description="Дізнатися свій Telegram ID"),
        BotCommand(command="admin", description="Адміністративна панель (тільки адміни)"),
    ])

    # Broadcast workers
    app["broadcast_queue"] = broadcast_queue
    app["broadcast_workers"] = await start_broadcast_workers(bot, app["db_pool"], redis, broadcast_queue)

async def on_cleanup(app: web.Application):
    logger.info("Graceful shutdown started")
    await stop_broadcast_workers(app["broadcast_workers"], broadcast_queue)
    await close_db_pool(app["db_pool"])
    await app["redis"].aclose()
    logger.info("Graceful shutdown completed")

def main():
    app = create_app()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    port = int(os.environ.get("PORT", 8000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
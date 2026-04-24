import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from db.pool import create_db_pool
from bot.middlewares import setup_middlewares
from bot.handlers import setup_routers
from bot.instance import bot

logging.basicConfig(level=logging.INFO)

async def main():
    pool = await create_db_pool()
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    setup_middlewares(dp)
    setup_routers(dp)
    await bot.delete_webhook(drop_pending_updates=True)
    # Передаємо db_pool і redis=None прямо в контекст polling
    await dp.start_polling(bot, db_pool=pool, redis=None)

if __name__ == "__main__":
    asyncio.run(main())
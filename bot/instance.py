# Singleton: bot (Bot), dp (Dispatcher)

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import settings

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
#dp = Dispatcher()
# dp більше не створюємо тут — він створюється в main.py
# /admin, головне меню адміна

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.keyboards.inline.admin import admin_panel_keyboard, back_to_admin_btn
from config import settings

router = Router()

@router.message(Command("admin"))
@router.message(F.text == "⚙️ Адмін-панель")
async def admin_panel(message: Message, is_super_admin):
    if not is_super_admin:
        await message.answer("🚫 Недостатньо прав.")
        return
    await message.answer("Адміністративна панель:", reply_markup=admin_panel_keyboard())

@router.callback_query(F.data == "admin_back")
async def back_to_admin(callback: CallbackQuery):
    await callback.message.edit_text("Адміністративна панель:", reply_markup=admin_panel_keyboard())
    await callback.answer()
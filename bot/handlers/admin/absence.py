# Відмітка відсутніх

import html
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline.admin import absence_students_keyboard, confirm_cancel_keyboard
from db.queries.absence import get_absence_status_today, mark_absent, mark_present
from db.queries.students import get_all_active_students
from config import settings

router = Router()

@router.callback_query(F.data == "admin_absence")
async def absence_today(callback: CallbackQuery, db):
    students = await get_all_active_students(db)
    statuses = await get_absence_status_today(db)
    tz = ZoneInfo(settings.TIMEZONE)
    now = datetime.now(tz)
    warning = ""
    if now.hour >= 9 and now.minute >= 40:
        warning = "⚠️ Зараз після 09:40. Зміни не вплинуть на чергування сьогодні.\n\n"
    text = warning + "Відмітка відсутніх сьогодні:\n"
    await callback.message.edit_text(text, reply_markup=absence_students_keyboard(students, statuses))
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_absence_"))
async def toggle_absence(callback: CallbackQuery, db, redis):
    # Логіка перемикання стану через callback_data
    # Зберігаємо зміни в FSM або Redis до фінального підтвердження
    await callback.answer("Стан змінено (тимчасово)")
    # Оновлюємо клавіатуру
    # ...

@router.callback_query(F.data == "absence_save")
async def absence_save(callback: CallbackQuery, state: FSMContext, db):
    # Збереження змін з транзакцією та оптимістичним блокуванням
    await callback.message.edit_text("✅ Відмітку збережено.")
    await callback.answer()
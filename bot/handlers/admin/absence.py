import html
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
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
    text = warning + "🩺 Відмітка відсутніх сьогодні:\n\n<i>Натискайте на учня, щоб змінити статус</i>"
    await callback.message.edit_text(
        text,
        reply_markup=absence_students_keyboard(students, statuses),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_absence_"))
async def toggle_absence(callback: CallbackQuery, db):
    student_id = int(callback.data.split("_")[2])
    
    # Отримуємо поточний статус
    statuses = await get_absence_status_today(db)
    is_absent_now = statuses.get(student_id, False)
    
    # Інвертуємо: якщо був присутній → відмічаємо як відсутнього, і навпаки
    from datetime import date
    today = date.today()
    
    if is_absent_now:
        # Був відсутній → робимо присутнім
        await mark_present(db, student_id, today)
    else:
        # Був присутній → відмічаємо як відсутнього
        await mark_absent(db, student_id, today)
    
    # Отримуємо оновлені статуси
    students = await get_all_active_students(db)
    updated_statuses = await get_absence_status_today(db)
    
    # Оновлюємо клавіатуру
    await callback.message.edit_reply_markup(
        reply_markup=absence_students_keyboard(students, updated_statuses)
    )
    await callback.answer("✅ Статус оновлено!")

@router.callback_query(F.data == "absence_back")
async def absence_back(callback: CallbackQuery):
    from bot.keyboards.inline.admin import admin_panel_keyboard
    await callback.message.edit_text(
        "Адміністративна панель:",
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()
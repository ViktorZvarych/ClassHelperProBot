import html
from datetime import datetime, date
from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from db.queries.absence import get_absence_status_today, mark_absent, mark_present
from db.queries.students import get_all_active_students
from bot.keyboards.inline.admin import absence_students_keyboard
from config import settings
from db.queries.absence import get_absence_last_5_days
from bot.keyboards.inline.admin import back_to_admin_btn

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
    
    statuses = await get_absence_status_today(db)
    is_absent_now = statuses.get(student_id, False)
    
    today = date.today()  # тепер date імпортовано зверху
    
    if is_absent_now:
        await mark_present(db, student_id, today)
    else:
        await mark_absent(db, student_id, today)
    
    students = await get_all_active_students(db)
    updated_statuses = await get_absence_status_today(db)
    
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
    
@router.callback_query(F.data == "admin_absence_5_days")
async def absence_5_days(callback: CallbackQuery, db):
    records = await get_absence_last_5_days(db)
    if not records:
        await callback.message.edit_text(
            "📭 За останні 5 днів відсутніх не зафіксовано.",
            reply_markup=back_to_admin_btn()
        )
        await callback.answer()
        return

    text = "📊 <b>Відсутні за останні 5 днів:</b>\n\n"
    for day_str, names in records.items():
        if names:
            text += f"🔹 {day_str}: {', '.join(html.escape(n) for n in names)}\n"
        else:
            text += f"🔹 {day_str}: немає\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
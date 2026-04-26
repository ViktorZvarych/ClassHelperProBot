import html
from datetime import date, datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from zoneinfo import ZoneInfo
from config import settings
from bot.keyboards.inline.homework import homework_menu_keyboard
from bot.keyboards.inline.common import cancel_button
from bot.states.fsm import GetHomeworkByDate
from services.schedule import is_school_day, get_timetable_for_date, get_week_type, format_date_uk, parse_date_input
from db.queries.schedule import get_week_config
from db.queries.homework import get_homework_for_subjects
from db.queries.subjects import get_all_subjects

router = Router()

@router.message(F.text == "📚 Домашнє завдання")
async def homework_menu(message: Message):
    await message.answer("Оберіть період:", reply_markup=homework_menu_keyboard())

# ============ НА СЬОГОДНІ ============

@router.callback_query(F.data == "hw_today")
async def hw_today(callback: CallbackQuery, db, redis, student):
    tz = ZoneInfo(settings.TIMEZONE)
    target = datetime.now(tz).date()
    await show_homework(callback.message, target, db, redis, student, is_first=True)
    await callback.answer()

# ============ НА 3 ДНІ (завтра + 2) ============

@router.callback_query(F.data == "hw_3_days")
async def hw_3_days(callback: CallbackQuery, db, redis, student):
    tz = ZoneInfo(settings.TIMEZONE)
    tomorrow = datetime.now(tz).date() + timedelta(days=1)
    for offset in range(3):
        target = tomorrow + timedelta(days=offset)
        await show_homework(callback.message, target, db, redis, student, is_first=(offset == 0))
    await callback.answer()

# ============ ОСНОВНА ФУНКЦІЯ ПОКАЗУ ДЗ ============

async def show_homework(msg: Message, target_date: date, db, redis, student, is_first: bool = False):
    school_day, reason = await is_school_day(target_date, db)
    if not school_day:
        reason_text = "вихідний" if reason == "weekend" else "канікули"
        day_label = "Завтра" if is_first else format_date_uk(target_date)
        await msg.answer(f"📭 {day_label} — {reason_text}, уроків немає.")
        return

    week_cfg = await get_week_config(db)
    if not week_cfg:
        await msg.answer("⚙️ Конфігурацію розкладу не налаштовано.")
        return

    week_type = get_week_type(target_date, week_cfg["semester_start"], week_cfg["first_week_type"])
    lessons = await get_timetable_for_date(target_date, student["group_name"], week_type, db, redis)

    if not lessons:
        day_label = "Завтра" if is_first else format_date_uk(target_date)
        await msg.answer(f"📭 Розклад на {day_label} порожній, ДЗ відсутнє.")
        return

    subject_ids = [l["subject_id"] for l in lessons if l.get("subject_id")]
    hw_map = await get_homework_for_subjects(subject_ids, target_date, db)

    # Формуємо заголовок
    date_str = format_date_uk(target_date)
    if is_first:
        header = f"📚 Домашнє завдання на Завтра, {date_str}:"
    else:
        header = f"📚 Домашнє завдання на {date_str}:"

    text = header + "\n" + "─" * 30 + "\n\n"
    for lesson in lessons:
        line = f"{lesson['lesson_num']}️⃣ {html.escape(lesson['subject_name'])}"
        hw = hw_map.get(lesson["subject_id"]) if lesson.get("subject_id") else None
        if hw:
            desc = html.escape(hw["description"])
            if hw["is_control"]:
                line += f" --- 🚨 Контрольна робота — {desc}"
            else:
                line += f" --- {desc}"
        else:
            line += " --- ✅ Нічого не задано"
        text += line + "\n\n"

    await msg.answer(text)
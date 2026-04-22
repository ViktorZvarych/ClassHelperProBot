# Домашнє завдання

import html
from datetime import date, datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from zoneinfo import ZoneInfo
from config import settings
from bot.keyboards.inline.homework import homework_menu_keyboard, back_to_homework_menu_btn
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

@router.callback_query(F.data == "hw_tomorrow")
async def hw_tomorrow(callback: CallbackQuery, db, redis, student):
    tz = ZoneInfo(settings.TIMEZONE)
    target = datetime.now(tz).date() + timedelta(days=1)
    await show_homework(callback.message, target, db, redis, student)
    await callback.answer()

@router.callback_query(F.data == "hw_day_after")
async def hw_day_after(callback: CallbackQuery, db, redis, student):
    tz = ZoneInfo(settings.TIMEZONE)
    target = datetime.now(tz).date() + timedelta(days=2)
    await show_homework(callback.message, target, db, redis, student)
    await callback.answer()

@router.callback_query(F.data == "hw_by_date")
async def hw_by_date_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📅 Введіть дату у форматі ДД.ММ.РРРР:",
        reply_markup=cancel_button()
    )
    await state.set_state(GetHomeworkByDate.waiting_date)
    await callback.answer()

@router.message(StateFilter(GetHomeworkByDate.waiting_date))
async def hw_date_input(message: Message, state: FSMContext, db, redis, student):
    date_str = message.text.strip()
    target_date = parse_date_input(date_str)
    if target_date is None:
        await message.answer("❌ Невірний формат або неіснуюча дата. Спробуйте ще раз: ДД.ММ.РРРР")
        return
    await state.clear()
    await show_homework(message, target_date, db, redis, student)

async def show_homework(msg: Message, target_date: date, db, redis, student):
    school_day, reason = await is_school_day(target_date, db)
    if not school_day:
        await msg.answer("📭 На цей день немає уроків (вихідний або канікули).")
        return

    week_cfg = await get_week_config(db)
    if not week_cfg:
        await msg.answer("⚙️ Конфігурацію розкладу не налаштовано.")
        return

    week_type = get_week_type(target_date, week_cfg["semester_start"], week_cfg["first_week_type"])
    lessons = await get_timetable_for_date(target_date, student["group_name"], week_type, db, redis)

    if not lessons:
        await msg.answer("📭 Розклад на цей день порожній, ДЗ відсутнє.")
        return

    subject_ids = [l["subject_id"] for l in lessons]
    hw_map = await get_homework_for_subjects(subject_ids, target_date, db)

    date_str = format_date_uk(target_date)
    text = f"📚 Домашнє завдання на {date_str}:\n\n"
    for lesson in lessons:
        line = f"{lesson['lesson_num']}️⃣ {html.escape(lesson['subject_name'])}"
        hw = hw_map.get(lesson["subject_id"])
        if hw:
            desc = html.escape(hw["description"])
            if hw["is_control"]:
                line += f"\n   🚨 Контрольна робота — {desc}"
            else:
                line += f"\n   {desc}"
        else:
            line += "\n   ✅ Нічого не задано"
        text += line + "\n\n"
    await msg.answer(text)
# Розклад

import html
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from services.schedule import get_week_type, is_school_day, get_timetable_for_date, format_date_uk
from db.queries.schedule import get_week_config
from db.queries.duty import get_duty_for_date
from config import settings

router = Router()

@router.message(F.text == "📅 Розклад сьогодні")
async def schedule_today(message: Message, db, redis, student):
    tz = ZoneInfo(settings.TIMEZONE)
    target = datetime.now(tz).date()
    await show_schedule(message, target, db, redis, student)

@router.message(F.text == "📆 Розклад завтра")
async def schedule_tomorrow(message: Message, db, redis, student):
    tz = ZoneInfo(settings.TIMEZONE)
    target = datetime.now(tz).date() + timedelta(days=1)
    await show_schedule(message, target, db, redis, student)

async def show_schedule(msg: Message, target_date: date, db, redis, student):
    week_cfg = await get_week_config(db)
    if not week_cfg:
        await msg.answer("⚙️ Конфігурацію розкладу не налаштовано. Зверніться до адміністратора.")
        return

    school_day, reason = await is_school_day(target_date, db)
    if not school_day:
        day_word = "Сьогодні" if target_date == date.today() else "Завтра"
        reason_text = "вихідний" if reason == "weekend" else "канікули"
        await msg.answer(f"😴 {day_word} — ненавчальний день ({reason_text}).\nВідпочивайте! 🎉")
        return

    week_type = get_week_type(target_date, week_cfg["semester_start"], week_cfg["first_week_type"])
    lessons = await get_timetable_for_date(target_date, student["group_name"], week_type, db, redis)

    if not lessons:
        await msg.answer("📭 Розклад на цей день відсутній")
        return

    date_str = format_date_uk(target_date)
    text = f"📆 {date_str} ({'Чисельник' if week_type == 'numerator' else 'Знаменник'})\n\n"
    for lesson in lessons:
        line = f"{lesson['lesson_num']}️⃣ {html.escape(lesson['subject_name'])}"
        if lesson.get('cabinet'):
            line += f" — каб. {html.escape(lesson['cabinet'])}"
        if lesson.get('is_control'):
            line += " 🚨 Контрольна робота"
        text += line + "\n"

    # Додати чергових, якщо є
    duty_list = await get_duty_for_date(target_date, db)
    if duty_list:
        text += "\n🧹 Чергові на сьогодні:\n"
        for d in duty_list:
            name = html.escape(d["full_name"])
            if d.get("replaced_by_name"):
                text += f"• {name} (замість відсутнього {html.escape(d['replaced_by_name'])})\n"
            else:
                text += f"• {name}\n"
    await msg.answer(text)
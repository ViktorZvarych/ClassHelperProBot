# Вечірній cron

import json
import logging
from datetime import date, timedelta
from zoneinfo import ZoneInfo
from config import settings
from services.schedule import is_school_day, get_week_type, format_date_uk, get_timetable_for_date
from services.duty_algorithm import calculate_duty_students
from db.queries.schedule import get_week_config
from db.queries.homework import get_homework_for_subjects
from db.queries.students import get_students_by_ids

logger = logging.getLogger(__name__)

async def run_evening_cron(app):
    # Перевірки токена, локів, idempotency виконуються в routes
    pool = app["db_pool"]
    redis = app["redis"]
    bot = app["bot"]
    tz = ZoneInfo(settings.TIMEZONE)
    today = datetime.now(tz).date()
    tomorrow = today + timedelta(days=1)

    # Перевірка навчального дня
    school, _ = await is_school_day(tomorrow, pool)
    if not school:
        return {"status": "skipped", "reason": "not_school_day"}

    # Розрахунок чергових
    duty_ids = await calculate_duty_students(tomorrow, pool)
    if not duty_ids:
        logger.error("No duty students calculated for tomorrow")
        return {"status": "error", "reason": "no_students"}

    # Отримання розкладу та ДЗ
    week_cfg = await get_week_config(pool)
    week_type = get_week_type(tomorrow, week_cfg["semester_start"], week_cfg["first_week_type"])
    # Для групи 'all' (спрощено), в реальності треба враховувати підгрупи чергових
    lessons = await get_timetable_for_date(tomorrow, "all", week_type, pool, redis)
    subject_ids = [l["subject_id"] for l in lessons]
    hw_map = await get_homework_for_subjects(subject_ids, tomorrow, pool)

    # Формування тексту повідомлення
    date_str = format_date_uk(tomorrow)
    text = f"🌙 Вечірній звіт на завтра, {date_str} ({'Чисельник' if week_type=='numerator' else 'Знаменник'})\n\n📚 Домашнє завдання:\n"
    for lesson in lessons:
        hw = hw_map.get(lesson["subject_id"])
        line = f"{lesson['lesson_num']}️⃣ {lesson['subject_name']}: "
        if hw:
            line += hw["description"]
            if hw["is_control"]:
                line += " 🚨"
        else:
            line += "нічого не задано"
        text += line + "\n"
    text += "\n🧹 Попередні чергові на завтра:\n"
    duty_students = await get_students_by_ids(duty_ids, pool)
    for s in duty_students:
        text += f"• {s['full_name']}\n"
    text += "\nℹ️ Остаточний список буде уточнено вранці (09:45) після відмітки відсутніх."

    # Надсилання в групу
    msg = await bot.send_message(settings.GROUP_CHAT_ID, text)
    # Збереження в bot_messages
    payload = {"duty_students": duty_ids}
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO bot_messages (chat_id, message_id, type, duty_date, evening_payload)
            VALUES ($1, $2, 'evening_duty', $3, $4)
            ON CONFLICT (chat_id, type, duty_date)
            DO UPDATE SET message_id = EXCLUDED.message_id, evening_payload = EXCLUDED.evening_payload
        """, settings.GROUP_CHAT_ID, msg.message_id, tomorrow, json.dumps(payload))
    return {"status": "success"}
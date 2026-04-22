# Скидання навчального року

import logging
from datetime import date
from zoneinfo import ZoneInfo
from config import settings
from services.notifications import notify_admins
from db.queries.class_info import get_class_info, update_class_info

logger = logging.getLogger(__name__)

async def run_reset_academic_year(app):
    pool = app["db_pool"]
    tz = ZoneInfo(settings.TIMEZONE)
    today = datetime.now(tz).date()
    if today.month != 9 or today.day != 1:
        return {"status": "skipped", "reason": "not_september_1"}

    async with pool.acquire() as conn:
        # Скидання чергувань
        await conn.execute("UPDATE students SET last_duty_date = NULL, consecutive_duty_skip = 0, updated_at = now() WHERE is_active = true")

        # Архівування duty_log
        result = await conn.fetchval("""
            WITH moved AS (
                INSERT INTO duty_log_archive (id, duty_date, student_id, status, replaced_by_id, created_at, updated_at)
                SELECT id, duty_date, student_id, status, replaced_by_id, created_at, updated_at
                FROM duty_log
                WHERE duty_date < (SELECT academic_year_start FROM class_info WHERE id = 1)
                RETURNING id
            )
            SELECT COUNT(*) FROM moved
        """)
        await conn.execute("DELETE FROM duty_log WHERE duty_date < (SELECT academic_year_start FROM class_info WHERE id = 1)")

        # Оновлення week_config
        september_1 = date(today.year, 9, 1)
        await conn.execute("""
            INSERT INTO week_config (id, semester_start, first_week_type, is_active)
            VALUES (1, $1, (SELECT first_week_type FROM week_config WHERE id = 1), true)
            ON CONFLICT (id) DO UPDATE SET semester_start = EXCLUDED.semester_start
        """, september_1)

        # Збільшення номера класу
        info = await get_class_info(pool)
        if info["class_number"] < 11:
            new_number = info["class_number"] + 1
            await update_class_info(conn, new_number, info["class_letter"])
        else:
            await notify_admins("🎓 Клас досяг 11-го року навчання. Оновіть вручну.")

        await notify_admins(f"✅ Скидання навчального року виконано. Архівовано {result} записів чергувань.")
    return {"status": "success"}
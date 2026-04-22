# Ранковий cron

import json
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo
from config import settings
from services.schedule import is_school_day
from services.duty_algorithm import calculate_duty_students_with_lock
from db.queries.students import get_students_by_ids

logger = logging.getLogger(__name__)

async def run_morning_cron(app):
    pool = app["db_pool"]
    redis = app["redis"]
    bot = app["bot"]
    tz = ZoneInfo(settings.TIMEZONE)
    today = datetime.now(tz).date()

    school, _ = await is_school_day(today, pool)
    if not school:
        return {"status": "skipped", "reason": "not_school_day"}

    async with pool.acquire() as conn:
        async with conn.transaction(isolation='repeatable_read'):
            # Крок A: вибір кандидатів з блокуванням
            final_duty_ids = await calculate_duty_students_with_lock(today, pool)

            # Крок B: отримання вечірнього payload
            row = await conn.fetchrow("""
                SELECT message_id, evening_payload FROM bot_messages
                WHERE chat_id = $1 AND type = 'evening_duty' AND duty_date = $2
            """, settings.GROUP_CHAT_ID, today)
            evening_ids = []
            if row:
                evening_ids = row["evening_payload"]["duty_students"]
                # Знайти відсутніх серед вечірніх
                absent_rows = await conn.fetch("""
                    SELECT student_id FROM absence_log
                    WHERE student_id = ANY($1) AND absent_date = $2 AND is_cancelled = false
                """, evening_ids, today)
                absent_from_evening = [r["student_id"] for r in absent_rows]
            else:
                absent_from_evening = []
                logger.warning(f"Evening report not found for {today}")

            # Крок C: запис у duty_log з урахуванням замін
            new_in_morning = [id for id in final_duty_ids if id not in evening_ids]
            confirmed_from_evening = [id for id in final_duty_ids if id in evening_ids]

            # Пари відсутній -> замінюючий
            replacement_pairs = list(zip(sorted(absent_from_evening), sorted(new_in_morning)))
            for absent_id, repl_id in replacement_pairs:
                await conn.execute("""
                    INSERT INTO duty_log (duty_date, student_id, status, replaced_by_id)
                    VALUES ($1, $2, 'replaced', $3)
                    ON CONFLICT (duty_date, student_id)
                    DO UPDATE SET status = 'replaced', replaced_by_id = EXCLUDED.replaced_by_id, updated_at = now()
                """, today, absent_id, repl_id)
                await conn.execute("""
                    INSERT INTO duty_log (duty_date, student_id, status, replaced_by_id)
                    VALUES ($1, $2, 'pending', NULL)
                    ON CONFLICT (duty_date, student_id) DO NOTHING
                """, today, repl_id)

            for confirmed_id in confirmed_from_evening:
                await conn.execute("""
                    INSERT INTO duty_log (duty_date, student_id, status, replaced_by_id)
                    VALUES ($1, $2, 'pending', NULL)
                    ON CONFLICT (duty_date, student_id) DO NOTHING
                """, today, confirmed_id)

            # Відсутні без заміни
            paired_absent = [pair[0] for pair in replacement_pairs]
            for absent_id in absent_from_evening:
                if absent_id not in paired_absent:
                    await conn.execute("""
                        INSERT INTO duty_log (duty_date, student_id, status, replaced_by_id)
                        VALUES ($1, $2, 'absent', NULL)
                        ON CONFLICT (duty_date, student_id)
                        DO UPDATE SET status = 'absent', updated_at = now()
                    """, today, absent_id)

            # Крок D: інкремент consecutive_duty_skip
            if row:  # тільки якщо був вечірній звіт
                for absent_id in absent_from_evening:
                    await conn.execute("""
                        UPDATE students SET consecutive_duty_skip = consecutive_duty_skip + 1, updated_at = now()
                        WHERE id = $1
                    """, absent_id)

    # Крок E: оновлення повідомлення
    # ... (реалізувати редагування або нове повідомлення)
    return {"status": "success"}
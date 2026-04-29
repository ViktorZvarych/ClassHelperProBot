import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import settings
from db.queries.election import get_active_election, get_non_voters, get_candidates_by_ids
from db.queries.students import get_all_active_students
from services.notifications import notify_admins

logger = logging.getLogger(__name__)

async def run_election_reminder(app):
    """
    Cron-завдання для нагадувань про вибори.
    Виконується кожні 6 годин.
    """
    pool = app["db_pool"]
    bot = app["bot"]
    tz = ZoneInfo(settings.TIMEZONE)
    now = datetime.now(tz)

    async with pool.acquire() as conn:
        active = await get_active_election(conn)
        if not active:
            return {"status": "skipped", "reason": "no_active_election"}

        election_id = active['id']
        started_at = active['started_at'].astimezone(tz)
        ends_at = started_at + timedelta(hours=24)
        remaining = ends_at - now

        # Якщо час вийшов — завершити вибори
        if remaining.total_seconds() <= 0:
            from services.election_service import finalize_election
            result = await finalize_election(election_id, pool)

            # Оголошення результатів у групі
            from db.queries.election import get_election_results
            results = await get_election_results(conn, election_id)
            
            text = "🗳️ <b>Вибори завершено!</b>\n\nРезультати:\n"
            for i, r in enumerate(results[:4], 1):
                student = await get_student_by_id(conn, r['candidate_id'])
                if student:
                    text += f"{i}. {student['full_name']} — {r['votes']} голосів\n"
            
            await bot.send_message(settings.GROUP_CHAT_ID, text, parse_mode="HTML")
            return {"status": "completed", "election_id": election_id}

        # Надіслати нагадування в групу
        hours_left = int(remaining.total_seconds() // 3600)
        minutes_left = int((remaining.total_seconds() % 3600) // 60)
        
        await bot.send_message(
            settings.GROUP_CHAT_ID,
            f"🗳️ <b>Нагадування про вибори!</b>\n\n"
            f"Залишилось часу: <b>{hours_left} год {minutes_left} хв</b>\n"
            f"Перейдіть у бот і натисніть 🗳️ Вибори, щоб проголосувати!",
            parse_mode="HTML"
        )

        # Надіслати особисті повідомлення тим, хто не проголосував
        non_voters = await get_non_voters(conn, election_id)
        for voter in non_voters:
            if voter.get('telegram_id'):
                try:
                    await bot.send_message(
                        voter['telegram_id'],
                        f"🗳️ <b>Ви ще не проголосували!</b>\n\n"
                        f"Залишилось часу: <b>{hours_left} год {minutes_left} хв</b>\n"
                        f"Натисніть 🗳️ Вибори у головному меню, щоб проголосувати.",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.warning(f"Failed to remind voter {voter['id']}: {e}")

    return {"status": "success", "election_id": election_id, "non_voters": len(non_voters)}
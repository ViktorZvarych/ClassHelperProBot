import html
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import settings
from bot.instance import bot as bot_instance
from db.queries.election import (
    get_active_election, create_election, finish_election,
    cast_vote, has_voted, get_election_results, get_non_voters,
    get_candidates_by_ids, set_student_role, reset_old_leadership,
    log_election_results, get_last_completed_election,
    get_election_results_by_place
)
from db.queries.students import get_all_active_students, get_student_by_id

logger = logging.getLogger(__name__)

def now_kyiv():
    return datetime.now(tz=ZoneInfo(settings.TIMEZONE))

async def start_no_confidence(initiator_id, pool):
    """Запустити вотум недовіри."""
    async with pool.acquire() as conn:
        active = await get_active_election(conn)
        if active:
            return False, "Вже триває інше голосування."

        election_id = await create_election(conn, 'no_confidence', initiator_id)
        return True, election_id

async def vote_no_confidence(election_id, voter_id, vote_yes, pool):
    """Проголосувати за/проти вотуму недовіри."""
    async with pool.acquire() as conn:
        candidate_id = -1 if vote_yes else -2
        success = await cast_vote(conn, election_id, voter_id, candidate_id)
        return success

async def check_no_confidence_result(election_id, pool):
    """Перевірити результати вотуму недовіри."""
    async with pool.acquire() as conn:
        results = await get_election_results(conn, election_id)
        yes_votes = sum(1 for r in results if r['candidate_id'] == -1)
        no_votes = sum(1 for r in results if r['candidate_id'] == -2)

        students = await get_all_active_students(conn)
        total_students = len(students)

        majority = total_students // 2 + 1
        return yes_votes >= majority, yes_votes, no_votes, total_students

async def start_regular_election(pool, initiator_id=None):
    """Запустити регулярні вибори."""
    async with pool.acquire() as conn:
        active = await get_active_election(conn)
        if active:
            return False, "Вже триває інше голосування."

        election_id = await create_election(conn, 'regular', initiator_id)
        return True, election_id

async def start_runoff_election(pool, parent_id, round_num):
    """Запустити переголосування (другий тур) при нічиї."""
    async with pool.acquire() as conn:
        active = await get_active_election(conn)
        if active:
            return False, "Вже триває інше голосування."

        election_id = await create_election(conn, 'runoff', None, parent_id, round_num)
        return True, election_id

async def vote_candidate(election_id, voter_id, candidate_id, pool):
    """Проголосувати за кандидата."""
    async with pool.acquire() as conn:
        return await cast_vote(conn, election_id, voter_id, candidate_id)

async def finalize_election(election_id, pool):
    """Завершити вибори та призначити старосту/замстаросту."""
    async with pool.acquire() as conn:
        await finish_election(conn, election_id)
        results = await get_election_results(conn, election_id)

        if not results:
            return "Ніхто не проголосував."

        # Відфільтрувати "технічні" candidate_id
        results = [r for r in results if r['candidate_id'] > 0]

        if not results:
            return "Немає голосів за кандидатів."

        # Знайти максимальну кількість голосів
        max_votes = results[0]['votes']
        first_place = [r for r in results if r['votes'] == max_votes]

        # Знайти другу кількість голосів (якщо є)
        second_votes = None
        for r in results:
            if r['votes'] < max_votes:
                second_votes = r['votes']
                break

        if second_votes:
            second_place = [r for r in results if r['votes'] == second_votes]
        else:
            second_place = []

        # Якщо перше місце зайняв один кандидат
        if len(first_place) == 1:
            winner_id = first_place[0]['candidate_id']
            
            # Отримати імена для повідомлення
            old_starosta = await conn.fetchrow(
                "SELECT full_name FROM students WHERE role = 'starosta' AND is_active = true"
            )
            old_zam = await conn.fetchrow(
                "SELECT full_name FROM students WHERE role = 'zamstarosta' AND is_active = true"
            )
            winner = await get_student_by_id(conn, winner_id)

            await reset_old_leadership(conn)
            await set_student_role(conn, winner_id, 'starosta')

            # Якщо друге місце зайняв один кандидат
            zam_name = None
            if len(second_place) == 1:
                zam_id = second_place[0]['candidate_id']
                await set_student_role(conn, zam_id, 'zamstarosta')
                zam = await get_student_by_id(conn, zam_id)
                zam_name = zam['full_name'] if zam else None

            # Логувати результати
            await log_election_results(conn, election_id, first_place)
            if second_place:
                await log_election_results(conn, election_id, second_place)

            # Повідомлення в групу
            try:
                msg = "🗳️ <b>Результати виборів!</b>\n\n"
                if old_starosta:
                    msg += f"Попередній староста: {html.escape(old_starosta['full_name'])}\n"
                msg += f"🎓 <b>Новий староста:</b> {html.escape(winner['full_name']) if winner else 'Невідомо'}"
                
                if zam_name:
                    if old_zam:
                        msg += f"\nПопередній зам. старости: {html.escape(old_zam['full_name'])}"
                    msg += f"\n📎 <b>Новий зам. старости:</b> {html.escape(zam_name)}"
                
                # Додати топ-4 результатів
                msg += "\n\n<b>Топ кандидатів:</b>\n"
                for i, r in enumerate(results[:4], 1):
                    student = await get_student_by_id(conn, r['candidate_id'])
                    name = html.escape(student['full_name']) if student else f"ID {r['candidate_id']}"
                    msg += f"{i}. {name} — {r['votes']} голосів\n"

                await bot_instance.send_message(settings.GROUP_CHAT_ID, msg, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Failed to send election results to group: {e}")

            return "starosta_elected"

        # Нічия за перше місце
        # Запускаємо переголосування
        try:
            # Отримати список кандидатів для повідомлення
            tied_names = []
            for r in first_place:
                student = await get_student_by_id(conn, r['candidate_id'])
                if student:
                    tied_names.append(html.escape(student['full_name']))
            
            await bot_instance.send_message(
                settings.GROUP_CHAT_ID,
                f"🔄 <b>Нічия у виборах!</b>\n\n"
                f"Кандидати набрали однакову кількість голосів:\n"
                f"{', '.join(tied_names)}\n\n"
                f"Буде проведено переголосування.",
                parse_mode="HTML"
            )
            
            # Запустити переголосування
            success, new_id = await start_runoff_election(pool, election_id, round=1)
            if success:
                return "runoff_started"
        except Exception as e:
            logger.error(f"Failed to start runoff: {e}")

        return "tie"


async def resign_zamstarosta(conn, zam_student_id, pool):
    """Скласти повноваження замстарости. Призначити 3-є місце з останніх виборів."""
    last_election = await get_last_completed_election(conn)
    
    if last_election:
        # Отримати 3-є місце
        third_place = await get_election_results_by_place(conn, last_election['id'], 3)
        if third_place:
            new_zam_id = third_place[0]['candidate_id']
            await set_student_role(conn, zam_student_id, 'student')
            await set_student_role(conn, new_zam_id, 'zamstarosta')
            
            new_zam = await get_student_by_id(conn, new_zam_id)
            return new_zam['full_name'] if new_zam else None
    
    # Якщо немає історичних даних — просто скинути роль
    await set_student_role(conn, zam_student_id, 'student')
    return None
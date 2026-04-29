import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import settings
from db.queries.election import (
    get_active_election, create_election, finish_election,
    cast_vote, has_voted, get_election_results, get_non_voters,
    get_candidates_by_ids, set_student_role, reset_old_leadership,
    log_election_results, get_last_completed_election,
    get_election_results_by_place
)
from db.queries.students import get_all_active_students

logger = logging.getLogger(__name__)

def now_kyiv():
    return datetime.now(tz=ZoneInfo(settings.TIMEZONE))

async def start_no_confidence(initiator_id, pool):
    """Запустити вотум недовіри."""
    async with pool.acquire() as conn:
        # Перевірити, чи немає активного голосування
        active = await get_active_election(conn)
        if active:
            return False, "Вже триває інше голосування."

        election_id = await create_election(conn, 'no_confidence', initiator_id)
        return True, election_id

async def vote_no_confidence(election_id, voter_id, vote_yes, pool):
    """Проголосувати за/проти вотуму недовіри."""
    async with pool.acquire() as conn:
        # У вотумі недовіри голосуємо "за" (candidate_id = -1) або "проти" (candidate_id = 0)
        # Для простоти зберігаємо vote_yes як candidate_id (1 = за, 0 = проти)
        # Але наша таблиця вимагає INT > 0. Використаємо костиль: candidate_id = -1 для "за", -2 для "проти"
        candidate_id = -1 if vote_yes else -2
        success = await cast_vote(conn, election_id, voter_id, candidate_id)
        return success

async def check_no_confidence_result(election_id, pool):
    """Перевірити результати вотуму недовіри."""
    async with pool.acquire() as conn:
        results = await get_election_results(conn, election_id)
        yes_votes = sum(1 for r in results if r['candidate_id'] == -1)
        no_votes = sum(1 for r in results if r['candidate_id'] == -2)

        # Отримати загальну кількість активних студентів
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
            await reset_old_leadership(conn)
            await set_student_role(conn, winner_id, 'starosta')

            # Якщо друге місце зайняв один кандидат
            if len(second_place) == 1:
                zam_id = second_place[0]['candidate_id']
                await set_student_role(conn, zam_id, 'zamstarosta')

            # Логувати результати
            await log_election_results(conn, election_id, first_place)
            if second_place:
                await log_election_results(conn, election_id, second_place)

            return "starosta_elected"

        # Нічия за перше місце
        return "tie"
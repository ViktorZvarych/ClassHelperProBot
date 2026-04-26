# Логіка розкладу та типу тижня

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from config import settings
import json
from db.queries.schedule import get_week_config

def get_week_type(target_date: date, semester_start: date, first_week_type: str) -> str:
    days_since_start = (target_date - semester_start).days
    weeks_since_start = days_since_start // 7
    if weeks_since_start % 2 == 0:
        return first_week_type
    else:
        return 'denominator' if first_week_type == 'numerator' else 'numerator'

def format_date_uk(d: date) -> str:
    days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]
    months = ["січня", "лютого", "березня", "квітня", "травня", "червня",
              "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]
    return f"{days[d.weekday()]}, {d.day} {months[d.month-1]}"

def parse_date_input(s: str) -> date | None:
    try:
        return datetime.strptime(s.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None

async def is_school_day(target_date: date, conn) -> tuple[bool, str]:
    if target_date.weekday() >= 5:
        return False, 'weekend'
    row = await conn.fetchrow(
        "SELECT 1 FROM holidays WHERE $1 BETWEEN start_date AND end_date LIMIT 1",
        target_date
    )
    if row:
        return False, 'holiday'
    return True, ''

async def get_timetable_for_date(target_date, group_name, week_type, conn, redis):
    cache_key = f"timetable:{target_date.isoformat()}:{group_name}:{week_type}"
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

    day_of_week = target_date.weekday()
    rows = await conn.fetch("""
        SELECT t.lesson_num, t.subject_id, s.name AS subject_name, t.cabinet, t.teacher, t.week_type
        FROM timetable t
        JOIN subjects s ON s.id = t.subject_id
        WHERE t.day_of_week = $1
          AND (t.week_type = $2 OR t.week_type = 'both')
          AND (t.group_name = 'all' OR ($3 != 'all' AND t.group_name = $3))
        ORDER BY t.lesson_num
    """, day_of_week, week_type, group_name)
    lessons = [dict(r) for r in rows]
    if redis:
        await redis.setex(cache_key, 300, json.dumps(lessons, default=str))
    return lessons

async def find_next_date_for_subject(subject_id: int, start_date: date, db, redis) -> date | None:
    """
    Знаходить найближчий навчальний день від start_date (включно),
    коли зазначений предмет є в розкладі (group_name='all').
    Шукає максимум 60 днів уперед.
    Повертає дату або None.
    """
    week_cfg = await get_week_config(db)
    if not week_cfg:
        return None
    semester_start = week_cfg["semester_start"]
    first_week_type = week_cfg["first_week_type"]

    for offset in range(60):
        candidate = start_date + timedelta(days=offset)
        school_day, _ = await is_school_day(candidate, db)
        if not school_day:
            continue
        day_of_week = candidate.weekday()
        week_type = get_week_type(candidate, semester_start, first_week_type)

        # Шукаємо урок саме для всього класу (group_name='all')
        query = """
            SELECT 1 FROM timetable
            WHERE day_of_week = $1
              AND subject_id = $2
              AND (week_type = $3 OR week_type = 'both')
              AND group_name = 'all'
            LIMIT 1
        """
        row = await db.fetchrow(query, day_of_week, subject_id, week_type)
        if row:
            return candidate
    return None
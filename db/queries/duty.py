from datetime import date, timedelta
from collections import defaultdict

async def get_duty_for_date(target_date: date, conn):
    """Отримати список чергових на конкретну дату (для відображення в розкладі)."""
    rows = await conn.fetch("""
        SELECT s.full_name, dl.status, r.full_name as replaced_by_name
        FROM duty_log dl
        JOIN students s ON dl.student_id = s.id
        LEFT JOIN students r ON dl.replaced_by_id = r.id
        WHERE dl.duty_date = $1
        ORDER BY dl.id
    """, target_date)
    return [dict(r) for r in rows]

async def get_duty_status_for_date(target_date: date, conn):
    """Отримати повну інформацію про статуси чергувань на дату."""
    rows = await conn.fetch("""
        SELECT dl.student_id, s.full_name, dl.status, r.full_name as replaced_by_name
        FROM duty_log dl
        JOIN students s ON dl.student_id = s.id
        LEFT JOIN students r ON dl.replaced_by_id = r.id
        WHERE dl.duty_date = $1
        ORDER BY s.full_name
    """, target_date)
    return [dict(r) for r in rows]

async def get_pending_duty_students(target_date: date, conn):
    """Отримати список учнів зі статусом 'pending' на вказану дату."""
    rows = await conn.fetch("""
        SELECT dl.student_id, s.full_name
        FROM duty_log dl
        JOIN students s ON dl.student_id = s.id
        WHERE dl.duty_date = $1 AND dl.status = 'pending'
    """, target_date)
    return [dict(r) for r in rows]

async def confirm_duty_completion(target_date: date, student_id: int, conn):
    """Підтвердити виконання чергування учнем."""
    async with conn.transaction():
        await conn.execute("""
            UPDATE duty_log
            SET status = 'completed', updated_at = now()
            WHERE duty_date = $1 AND student_id = $2 AND status = 'pending'
        """, target_date, student_id)
        await conn.execute("""
            UPDATE students
            SET last_duty_date = $1, consecutive_duty_skip = 0, updated_at = now()
            WHERE id = $2
        """, target_date, student_id)

async def get_duty_history(start_date: date, end_date: date, conn):
    """Отримати історію чергувань за період, згруповану за днями."""
    rows = await conn.fetch("""
        SELECT dl.duty_date, s.full_name, dl.status, r.full_name as replaced_by_name
        FROM duty_log dl
        JOIN students s ON dl.student_id = s.id
        LEFT JOIN students r ON dl.replaced_by_id = r.id
        WHERE dl.duty_date BETWEEN $1 AND $2
        ORDER BY dl.duty_date DESC, dl.id
    """, start_date, end_date)

    result = {}
    for row in rows:
        day_str = row["duty_date"].strftime("%d.%m (%a)")
        if day_str not in result:
            result[day_str] = []
        result[day_str].append(dict(row))
    return result
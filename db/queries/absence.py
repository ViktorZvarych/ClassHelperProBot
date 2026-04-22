from datetime import date, timedelta

async def mark_absent(conn, student_id, absent_date):
    await conn.execute("""
        INSERT INTO absence_log (student_id, absent_date, is_cancelled)
        VALUES ($1, $2, false)
        ON CONFLICT (student_id, absent_date)
        DO UPDATE SET is_cancelled = false, updated_at = now()
    """, student_id, absent_date)

async def mark_present(conn, student_id, absent_date):
    await conn.execute("""
        UPDATE absence_log SET is_cancelled = true, updated_at = now()
        WHERE student_id = $1 AND absent_date = $2
    """, student_id, absent_date)

async def get_absence_status_today(conn):
    today = date.today()
    rows = await conn.fetch("""
        SELECT student_id, is_cancelled FROM absence_log
        WHERE absent_date = $1
    """, today)
    return {r["student_id"]: not r["is_cancelled"] for r in rows}

async def get_absence_last_5_days(conn):
    end = date.today()
    start = end - timedelta(days=5)
    rows = await conn.fetch("""
        SELECT al.absent_date, s.full_name
        FROM absence_log al
        JOIN students s ON al.student_id = s.id
        WHERE al.absent_date BETWEEN $1 AND $2 AND al.is_cancelled = false
        ORDER BY al.absent_date DESC, s.full_name
    """, start, end)
    result = {}
    for r in rows:
        day_str = r["absent_date"].strftime("%d.%m (%a)")
        result.setdefault(day_str, []).append(r["full_name"])
    return result
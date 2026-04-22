async def get_duty_for_date(date, conn):
    rows = await conn.fetch("""
        SELECT s.full_name, dl.status, r.full_name as replaced_by_name
        FROM duty_log dl
        JOIN students s ON dl.student_id = s.id
        LEFT JOIN students r ON dl.replaced_by_id = r.id
        WHERE dl.duty_date = $1
        ORDER BY dl.id
    """, date)
    return [dict(r) for r in rows]

async def get_pending_duty_students(date, conn):
    rows = await conn.fetch("""
        SELECT dl.student_id, s.full_name
        FROM duty_log dl
        JOIN students s ON dl.student_id = s.id
        WHERE dl.duty_date = $1 AND dl.status = 'pending'
    """, date)
    return [dict(r) for r in rows]

async def confirm_duty_completion(date, student_id, conn):
    async with conn.transaction():
        await conn.execute("""
            UPDATE duty_log SET status = 'completed', updated_at = now()
            WHERE duty_date = $1 AND student_id = $2 AND status = 'pending'
        """, date, student_id)
        await conn.execute("""
            UPDATE students SET last_duty_date = $1, consecutive_duty_skip = 0, updated_at = now()
            WHERE id = $2
        """, date, student_id)

async def get_duty_history(start_date, end_date, conn):
    rows = await conn.fetch("""
        SELECT dl.duty_date, s.full_name, dl.status, r.full_name as replaced_by_name
        FROM duty_log dl
        JOIN students s ON dl.student_id = s.id
        LEFT JOIN students r ON dl.replaced_by_id = r.id
        WHERE dl.duty_date BETWEEN $1 AND $2
        ORDER BY dl.duty_date DESC, dl.id
    """, start_date, end_date)
    result = {}
    for r in rows:
        date_str = r["duty_date"].strftime("%d.%m (%a)")
        result.setdefault(date_str, []).append(dict(r))
    return result
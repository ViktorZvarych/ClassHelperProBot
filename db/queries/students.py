async def get_all_active_students(conn):
    rows = await conn.fetch("""
        SELECT id, full_name, role, group_name, telegram_id, consecutive_duty_skip
        FROM students WHERE is_active = true ORDER BY full_name
    """)
    return [dict(r) for r in rows]

async def get_students_list_with_debt(conn):
    rows = await conn.fetch("""
        SELECT full_name, role, consecutive_duty_skip
        FROM students WHERE is_active = true ORDER BY full_name
    """)
    return [dict(r) for r in rows]

async def get_active_students_telegram_ids(conn):
    rows = await conn.fetch("SELECT telegram_id FROM students WHERE is_active = true AND telegram_id IS NOT NULL")
    return [r["telegram_id"] for r in rows]

async def create_student(conn, full_name, group_name, role, telegram_id=None):
    return await conn.fetchval("""
        INSERT INTO students (full_name, group_name, role, telegram_id)
        VALUES ($1, $2, $3, $4) RETURNING id
    """, full_name, group_name, role, telegram_id)
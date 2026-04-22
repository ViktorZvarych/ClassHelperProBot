async def get_homework_for_subjects(subject_ids, due_date, conn):
    rows = await conn.fetch("""
        SELECT subject_id, description, is_control
        FROM homework
        WHERE subject_id = ANY($1::int[]) AND due_date = $2 AND is_active = true
        ORDER BY created_at DESC
    """, subject_ids, due_date)
    return {r["subject_id"]: dict(r) for r in rows}

async def add_homework(conn, subject_id, due_date, description, is_control, added_by):
    await conn.execute("""
        INSERT INTO homework (subject_id, due_date, description, is_control, added_by)
        VALUES ($1, $2, $3, $4, $5)
    """, subject_id, due_date, description, is_control, added_by)

async def get_upcoming_homework(conn, limit=14):
    rows = await conn.fetch("""
        SELECT h.id, s.name as subject_name, h.due_date, h.description, h.is_control
        FROM homework h
        JOIN subjects s ON h.subject_id = s.id
        WHERE h.is_active = true AND h.due_date >= CURRENT_DATE
        ORDER BY h.due_date
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]
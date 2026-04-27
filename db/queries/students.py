async def get_all_active_students(conn, include_guests: bool = False):
    if include_guests:
        rows = await conn.fetch("""
            SELECT id, full_name, role, group_name, telegram_id, consecutive_duty_skip
            FROM students WHERE is_active = true ORDER BY full_name
        """)
    else:
        rows = await conn.fetch("""
            SELECT id, full_name, role, group_name, telegram_id, consecutive_duty_skip
            FROM students WHERE is_active = true AND role != 'guest' ORDER BY full_name
        """)
    return [dict(r) for r in rows]

async def get_students_list_with_debt(conn):
    rows = await conn.fetch("""
        SELECT full_name, role, consecutive_duty_skip
        FROM students WHERE is_active = true AND role != 'guest' ORDER BY full_name
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

async def get_student_by_telegram_id(conn, telegram_id: int):
    row = await conn.fetchrow(
        """
        SELECT id, full_name, role, group_name, is_active, consecutive_duty_skip
        FROM students
        WHERE telegram_id = $1 AND is_active = true
        """,
        telegram_id
    )
    return dict(row) if row else None

async def get_student_by_id(conn, student_id: int):
    row = await conn.fetchrow(
        """
        SELECT id, full_name, role, group_name, is_active, consecutive_duty_skip, telegram_id
        FROM students
        WHERE id = $1
        """,
        student_id
    )
    return dict(row) if row else None

async def get_students_by_ids(conn, student_ids: list[int]):
    if not student_ids:
        return []
    rows = await conn.fetch(
        """
        SELECT id, full_name, role, group_name
        FROM students
        WHERE id = ANY($1::int[])
        ORDER BY full_name
        """,
        student_ids
    )
    return [dict(r) for r in rows]

async def update_student(conn, student_id: int, **kwargs):
    allowed_fields = {"full_name", "role", "group_name", "telegram_id", "is_active"}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    if not updates:
        return
    set_clause = ", ".join(f"{field} = ${i+2}" for i, field in enumerate(updates.keys()))
    values = list(updates.values())
    query = f"UPDATE students SET {set_clause}, updated_at = now() WHERE id = $1"
    await conn.execute(query, student_id, *values)

async def deactivate_student(conn, student_id: int):
    await conn.execute(
        "UPDATE students SET is_active = false, updated_at = now() WHERE id = $1",
        student_id
    )
    
async def get_student_with_class_name(conn, telegram_id: int):
    row = await conn.fetchrow(
        """
        SELECT s.id, s.full_name, s.role, s.group_name, s.is_active, s.consecutive_duty_skip,
               ci.class_number, ci.class_letter
        FROM students s
        CROSS JOIN class_info ci
        WHERE s.telegram_id = $1 AND s.is_active = true AND ci.id = 1
        """,
        telegram_id
    )
    if not row:
        return None
    result = dict(row)
    result["class_name"] = f"{result['class_number']}-{result['class_letter']}"
    return result
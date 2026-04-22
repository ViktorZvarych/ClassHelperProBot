async def get_week_config(conn):
    row = await conn.fetchrow("SELECT semester_start, first_week_type FROM week_config WHERE id = 1")
    return dict(row) if row else None
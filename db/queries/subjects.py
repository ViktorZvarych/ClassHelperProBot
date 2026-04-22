async def get_all_subjects(conn):
    rows = await conn.fetch("SELECT id, name FROM subjects ORDER BY name")
    return [dict(r) for r in rows]
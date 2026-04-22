async def get_all_holidays(conn):
    rows = await conn.fetch("SELECT id, start_date, end_date, description FROM holidays ORDER BY start_date")
    return [dict(r) for r in rows]

async def add_holiday(conn, start_date, end_date, description=None):
    await conn.execute("INSERT INTO holidays (start_date, end_date, description) VALUES ($1, $2, $3)",
                       start_date, end_date, description)

async def delete_holiday(conn, holiday_id):
    await conn.execute("DELETE FROM holidays WHERE id = $1", holiday_id)
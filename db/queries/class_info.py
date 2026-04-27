async def get_class_info(conn):
    row = await conn.fetchrow("SELECT class_number, class_letter FROM class_info WHERE id = 1")
    return dict(row)

async def update_class_info(conn, class_number, class_letter):
    await conn.execute(
        "UPDATE class_info SET class_number=$1, class_letter=$2, updated_at=now() WHERE id=1",
        class_number, class_letter
    )
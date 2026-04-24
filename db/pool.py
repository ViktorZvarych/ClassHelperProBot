import asyncpg
from config import settings

async def create_db_pool():
    # Примусово використовуємо IPv4 через параметри DSN
    dsn = settings.DATABASE_URL
    if "?" in dsn:
        dsn += "&family=4"
    else:
        dsn += "?family=4"
    return await asyncpg.create_pool(
        dsn,
        min_size=1,
        max_size=10,
        command_timeout=60,
        ssl='require'
    )

async def close_db_pool(pool):
    await pool.close()
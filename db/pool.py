import asyncpg
from config import settings

async def create_db_pool():
    dsn = settings.DATABASE_URL
    if "?family=4" not in dsn:
        if "?" in dsn:
            dsn += "&family=4"
        else:
            dsn += "?family=4"
    return await asyncpg.create_pool(
        dsn,
        min_size=1,
        max_size=10,
        command_timeout=60,
        ssl='require',
        statement_cache_size=0  # <-- вимикаємо кешування для pgbouncer
    )

async def close_db_pool(pool):
    await pool.close()
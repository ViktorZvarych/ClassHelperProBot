# create_pool, get_pool

import asyncpg
from config import settings

async def create_db_pool():
    return await asyncpg.create_pool(
        settings.DATABASE_URL,
        min_size=1,
        max_size=10,
        command_timeout=60
    )

async def close_db_pool(pool):
    await pool.close()
# Redis Lock + cron_runs idempotency

import logging
from datetime import date
from redis.asyncio import Redis
import asyncpg

logger = logging.getLogger(__name__)

async def acquire_cron_lock(redis: Redis, endpoint: str, run_date: date) -> bool:
    key = f"cron_lock:{endpoint}:{run_date.isoformat()}"
    return await redis.set(key, "1", nx=True, ex=30)

async def release_cron_lock(redis: Redis, endpoint: str, run_date: date):
    key = f"cron_lock:{endpoint}:{run_date.isoformat()}"
    await redis.delete(key)

async def mark_cron_run(pool: asyncpg.Pool, endpoint: str, run_date: date) -> bool:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO cron_runs (endpoint, run_date)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, endpoint, run_date)
        return row is not None
# asyncio.Queue + воркери

import asyncio
import logging
from dataclasses import dataclass
from typing import List
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
import asyncpg
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

@dataclass
class BroadcastTask:
    sender_id: int
    chat_ids: List[int]
    text: str
    retry_count: int = 0

broadcast_queue = asyncio.Queue()

async def broadcast_worker(bot: Bot, pool: asyncpg.Pool, redis: Redis, queue: asyncio.Queue):
    while True:
        task = await queue.get()
        try:
            for chat_id in task.chat_ids:
                try:
                    await bot.send_message(chat_id, task.text)
                    await asyncio.sleep(0.05)  # throttle
                except TelegramRetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                    # retry
                    await bot.send_message(chat_id, task.text)
                except TelegramForbiddenError:
                    logger.warning(f"User {chat_id} blocked bot")
                except Exception as e:
                    logger.error(f"Failed to send to {chat_id}: {e}")
                    # retry logic or save to failed_jobs
        except Exception as e:
            logger.exception("Worker error")
        finally:
            queue.task_done()

async def start_broadcast_workers(bot, pool, redis, queue):
    workers = []
    for _ in range(2):
        task = asyncio.create_task(broadcast_worker(bot, pool, redis, queue))
        workers.append(task)
    return workers

async def stop_broadcast_workers(workers, queue):
    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)
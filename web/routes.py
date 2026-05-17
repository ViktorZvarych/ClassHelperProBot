from aiohttp import web
import logging
from config import settings
from cron.evening import run_evening_cron
from cron.morning import run_morning_cron
from cron.reset_year import run_reset_academic_year
from cron.election_reminder import run_election_reminder
from cron.base import acquire_cron_lock, release_cron_lock, mark_cron_run
from bot.instance import bot
from aiogram.types import Update
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

async def ping(request):
    pool = request.app.get("db_pool")
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return web.json_response({"status": "ok", "db": "connected"})
        except Exception:
            return web.json_response({"status": "ok", "db": "error"})
    return web.json_response({"status": "ok"})

async def webhook_handler(request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.WEBHOOK_SECRET:
        return web.Response(status=403)
    try:
        data = await request.json()
        update = Update.model_validate(data)
        dp = request.app["dp"]  # беремо dp з app
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.exception("Webhook error")
    return web.Response(status=200)

async def cron_evening_handler(request):
    token = request.headers.get("X-Cron-Token")
    if token != settings.CRON_SECRET_TOKEN:
        return web.Response(status=403)
    tz = ZoneInfo(settings.TIMEZONE)
    today = datetime.now(tz).date()
    redis = request.app["redis"]
    pool = request.app["db_pool"]

    if not await acquire_cron_lock(redis, "evening", today):
        return web.json_response({"status": "skipped", "reason": "lock"})
    if not await mark_cron_run(pool, "evening", today):
        await release_cron_lock(redis, "evening", today)
        return web.json_response({"status": "skipped", "reason": "already_run"})

    try:
        result = await run_evening_cron(request.app)
    finally:
        await release_cron_lock(redis, "evening", today)
    return web.json_response(result)

async def cron_morning_handler(request):
    token = request.headers.get("X-Cron-Token")
    if token != settings.CRON_SECRET_TOKEN:
        return web.Response(status=403)
    tz = ZoneInfo(settings.TIMEZONE)
    today = datetime.now(tz).date()
    redis = request.app["redis"]
    pool = request.app["db_pool"]

    if not await acquire_cron_lock(redis, "morning", today):
        return web.json_response({"status": "skipped", "reason": "lock"})
    if not await mark_cron_run(pool, "morning", today):
        await release_cron_lock(redis, "morning", today)
        return web.json_response({"status": "skipped", "reason": "already_run"})

    try:
        result = await run_morning_cron(request.app)
    finally:
        await release_cron_lock(redis, "morning", today)
    return web.json_response(result)

async def cron_reset_handler(request):
    token = request.headers.get("X-Cron-Token")
    if token != settings.CRON_SECRET_TOKEN:
        return web.Response(status=403)
    tz = ZoneInfo(settings.TIMEZONE)
    today = datetime.now(tz).date()
    redis = request.app["redis"]
    pool = request.app["db_pool"]

    if not await acquire_cron_lock(redis, "reset_academic_year", today):
        return web.json_response({"status": "skipped", "reason": "lock"})
    if not await mark_cron_run(pool, "reset_academic_year", today):
        await release_cron_lock(redis, "reset_academic_year", today)
        return web.json_response({"status": "skipped", "reason": "already_run"})

    try:
        result = await run_reset_academic_year(request.app)
    finally:
        await release_cron_lock(redis, "reset_academic_year", today)
    return web.json_response(result)

async def cron_election_reminder_handler(request):
    token = request.headers.get("X-Cron-Token")
    if token != settings.CRON_SECRET_TOKEN:
        return web.Response(status=403)
    tz = ZoneInfo(settings.TIMEZONE)
    today = datetime.now(tz).date()
    redis = request.app["redis"]
    pool = request.app["db_pool"]

    if not await acquire_cron_lock(redis, "election_reminder", today):
        return web.json_response({"status": "skipped", "reason": "lock"})
    if not await mark_cron_run(pool, "election_reminder", today):
        await release_cron_lock(redis, "election_reminder", today)
        return web.json_response({"status": "skipped", "reason": "already_run"})

    try:
        result = await run_election_reminder(request.app)
    finally:
        await release_cron_lock(redis, "election_reminder", today)
    return web.json_response(result)

def setup_routes(app: web.Application):
    app.router.add_get("/ping", ping)
    app.router.add_post("/webhook", webhook_handler)
    app.router.add_get("/cron/evening", cron_evening_handler)
    app.router.add_get("/cron/morning", cron_morning_handler)
    app.router.add_get("/cron/reset_academic_year", cron_reset_handler)
    app.router.add_get("/cron/election_reminder", cron_election_reminder_handler)
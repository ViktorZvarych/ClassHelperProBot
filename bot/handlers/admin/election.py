import html
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from config import settings
from bot.keyboards.inline.admin import admin_panel_keyboard, back_to_admin_btn
from db.queries.election import (
    get_active_election, get_last_completed_election,
    get_election_results, get_election_results_by_place,
    get_candidates_by_ids
)
from db.queries.students import get_all_active_students, get_student_by_id
from services.election_service import (
    start_regular_election, finalize_election, start_runoff_election
)

router = Router()

# ========== ГОЛОВНЕ МЕНЮ КЕРУВАННЯ ВИБОРАМИ ==========

@router.callback_query(F.data == "admin_elections")
async def admin_elections_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗓 Призначити регулярні вибори", callback_data="admin_start_election")],
        [InlineKeyboardButton(text="👑 Призначити старосту вручну", callback_data="admin_assign_starosta_manual")],
        [InlineKeyboardButton(text="📜 Історія виборів", callback_data="admin_election_history")],
        [InlineKeyboardButton(text="🔍 Поточне голосування", callback_data="admin_current_election")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text("🗳️ <b>Керування виборами:</b>", reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# ========== ПРИЗНАЧИТИ ВИБОРИ ==========

@router.callback_query(F.data == "admin_start_election")
async def admin_start_election(callback: CallbackQuery, db, bot):
    active = await get_active_election(db)
    if active:
        await callback.message.edit_text(
            "❌ Вже триває інше голосування. Дочекайтесь його завершення.",
            reply_markup=back_to_admin_btn()
        )
        await callback.answer()
        return

    # Запитуємо підтвердження
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Так, запустити вибори", callback_data="admin_start_election_confirm")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="admin_elections")]
    ])
    await callback.message.edit_text(
        "🗓 <b>Запустити регулярні вибори?</b>\n\n"
        "Вибори триватимуть 24 години. Усі активні студенти (крім гостей) зможуть голосувати.",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_start_election_confirm")
async def admin_start_election_confirm(callback: CallbackQuery, pool, bot):
    try:
        success, result = await start_regular_election(pool)
        if success:
            # Оголошення в групі
            await bot.send_message(
                settings.GROUP_CHAT_ID,
                "🗳️ <b>Розпочато регулярні вибори!</b>\n\n"
                "Голосування триватиме 24 години.\n"
                "Перейдіть у бот і натисніть 🗳️ Вибори, щоб проголосувати.",
                parse_mode="HTML"
            )
            await callback.message.edit_text(
                f"✅ Вибори запущено! ID: {result}",
                reply_markup=admin_panel_keyboard()
            )
        else:
            await callback.message.edit_text(f"❌ {result}", reply_markup=back_to_admin_btn())
        await callback.answer()
    except Exception as e:
        await callback.message.edit_text(f"❌ Помилка: {e}", reply_markup=back_to_admin_btn())
        await callback.answer()

# ========== ПРИЗНАЧИТИ СТАРОСТУ ВРУЧНУ ==========

@router.callback_query(F.data == "admin_assign_starosta_manual")
async def admin_assign_starosta_manual(callback: CallbackQuery, db):
    students = await get_all_active_students(db)
    kb = []
    for s in students:
        role_icon = {"starosta": "🎓", "zamstarosta": "📎"}.get(s['role'], "👤")
        kb.append([InlineKeyboardButton(
            text=f"{role_icon} {s['full_name']}",
            callback_data=f"admin_assign_starosta_{s['id']}"
        )])
    kb.append([InlineKeyboardButton(text="↩️ Назад", callback_data="admin_elections")])

    await callback.message.edit_text(
        "👑 <b>Оберіть учня для призначення старостою:</b>\n\n"
        "<i>Поточний староста буде замінений.</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_assign_starosta_"))
async def admin_assign_starosta_execute(callback: CallbackQuery, db):
    student_id = int(callback.data.split("_")[3])
    student = await get_student_by_id(db, student_id)

    if not student:
        await callback.answer("❌ Учня не знайдено.", show_alert=True)
        return

    # Скинути попередніх
    await db.execute("UPDATE students SET role = 'student' WHERE role IN ('starosta', 'zamstarosta')")
    await db.execute("UPDATE students SET role = 'starosta', updated_at = now() WHERE id = $1", student_id)

    await callback.message.edit_text(
        f"✅ <b>{html.escape(student['full_name'])}</b> призначено старостою!",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# ========== ІСТОРІЯ ВИБОРІВ ==========

@router.callback_query(F.data == "admin_election_history")
async def admin_election_history(callback: CallbackQuery, db):
    rows = await db.fetch(
        """
        SELECT erl.election_id, e.election_type, erl.student_id, s.full_name,
               erl.place, erl.votes, erl.role_awarded, e.finished_at
        FROM election_results_log erl
        JOIN elections e ON erl.election_id = e.id
        JOIN students s ON erl.student_id = s.id
        ORDER BY e.finished_at DESC, erl.place ASC
        LIMIT 50
        """
    )

    if not rows:
        await callback.message.edit_text(
            "📭 Історія виборів порожня.",
            reply_markup=back_to_admin_btn()
        )
        await callback.answer()
        return

    text = "📜 <b>Історія виборів:</b>\n\n"
    current_election = None
    for r in rows:
        if r['election_id'] != current_election:
            text += f"🔹 Вибори #{r['election_id']} ({r['election_type']}) — завершено {r['finished_at'].strftime('%d.%m.%Y')}\n"
            current_election = r['election_id']
        role_awarded = f" — {r['role_awarded']}" if r['role_awarded'] else ""
        text += f"  {r['place']}. {html.escape(r['full_name'])} ({r['votes']} голосів){role_awarded}\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_elections")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# ========== ПОТОЧНЕ ГОЛОСУВАННЯ ==========

@router.callback_query(F.data == "admin_current_election")
async def admin_current_election(callback: CallbackQuery, db):
    active = await get_active_election(db)
    if not active:
        await callback.message.edit_text(
            "🔍 Немає активного голосування.",
            reply_markup=back_to_admin_btn()
        )
        await callback.answer()
        return

    results = await get_election_results(db, active['id'])
    tz = ZoneInfo(settings.TIMEZONE)
    now = datetime.now(tz)
    started = active['started_at'].astimezone(tz)
    ends = started + timedelta(hours=24)
    remaining = ends - now
    hours_left = max(0, remaining.total_seconds() // 3600)

    text = (
        f"🔍 <b>Поточне голосування #{active['id']}</b>\n\n"
        f"Тип: <b>{active['election_type']}</b>\n"
        f"Початок: {started.strftime('%d.%m.%Y %H:%M')}\n"
        f"Залишилось: <b>{int(hours_left)} годин</b>\n\n"
        f"<b>Проміжні результати:</b>\n"
    )

    for i, r in enumerate(results[:10], 1):
        student = await get_student_by_id(db, r['candidate_id'])
        name = html.escape(student['full_name']) if student else f"ID {r['candidate_id']}"
        text += f"{i}. {name} — {r['votes']} голосів\n"

    if not results:
        text += "Ще ніхто не проголосував.\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Оновити", callback_data="admin_current_election")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_elections")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
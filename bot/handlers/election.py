import html
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from config import settings
from bot.states.fsm import NoConfidenceVote, RegularElection, ResignStarosta, ResignZamStarosta
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.inline.election import (
    election_menu_keyboard, no_confidence_confirm_keyboard,
    vote_no_confidence_keyboard, resign_confirm_keyboard,
    candidate_list_keyboard
)
from services.election_service import (
    start_no_confidence, vote_no_confidence, check_no_confidence_result,
    start_regular_election, start_runoff_election, vote_candidate,
    finalize_election
)
from db.queries.election import (
    get_active_election, has_voted, get_non_voters,
    get_candidates_by_ids, get_last_completed_election,
    get_election_results_by_place
)
from db.queries.students import get_all_active_students, get_student_by_id

router = Router()

# ========== ГОЛОВНЕ МЕНЮ ВИБОРІВ ==========

@router.message(F.text == "🗳️ Вибори")
async def election_menu(message: Message, student):
    if not student:
        await message.answer("Спочатку зареєструйтесь через /start.")
        return

    # Додати кнопку "Скласти повноваження" для старости/замстарости
    kb = election_menu_keyboard()
    if student['role'] == 'starosta':
        kb.inline_keyboard.insert(1, [
            InlineKeyboardButton(text="📝 Скласти повноваження (староста)", callback_data="resign_starosta")
        ])
    elif student['role'] == 'zamstarosta':
        kb.inline_keyboard.insert(1, [
            InlineKeyboardButton(text="📝 Скласти повноваження (замстарости)", callback_data="resign_zamstarosta")
        ])

    await message.answer("🗳️ Меню виборів:", reply_markup=kb)

# ========== ІНФОРМАЦІЯ ==========

@router.callback_query(F.data == "election_info")
async def election_info(callback: CallbackQuery, db):
    # Отримати поточних старосту та замстаросту
    starosta = await db.fetchrow(
        "SELECT full_name FROM students WHERE role = 'starosta' AND is_active = true"
    )
    zam = await db.fetchrow(
        "SELECT full_name FROM students WHERE role = 'zamstarosta' AND is_active = true"
    )

    text = (
        "🗳️ <b>Інформація про вибори</b>\n\n"
        f"🎓 <b>Староста:</b> {html.escape(starosta['full_name']) if starosta else 'Не призначено'}\n"
        f"📎 <b>Зам. старости:</b> {html.escape(zam['full_name']) if zam else 'Не призначено'}\n\n"
        "<b>Правила виборів:</b>\n"
        "• Регулярні вибори проводяться на початку півріччя.\n"
        "• Кожен студент (крім гостей) може голосувати 1 раз.\n"
        "• Голосування триває 24 години.\n"
        "• Якщо кілька кандидатів набирають однакову кількість голосів — проводиться переголосування.\n\n"
        "<b>Вотум недовіри:</b>\n"
        "• Будь-який студент може ініціювати вотум недовіри.\n"
        "• Для успіху потрібно більшість голосів (50%+1).\n"
        "• У разі успіху — автоматично запускаються нові вибори.\n\n"
        "<b>Складання повноважень:</b>\n"
        "• Староста: запускає нові вибори.\n"
        "• Замстарости: призначається наступний за голосами з останніх виборів."
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

# ========== ВОТУМ НЕДОВІРИ ==========

@router.callback_query(F.data == "no_confidence_start")
async def no_confidence_start(callback: CallbackQuery, state: FSMContext, db, student):
    active = await get_active_election(db)
    if active:
        await callback.answer("❌ Вже триває інше голосування.", show_alert=True)
        return

    await callback.message.edit_text(
        "🚫 <b>Вотум недовіри</b>\n\n"
        "Ви впевнені, що хочете ініціювати вотум недовіри?\n"
        "Якщо вотум набере більшість голосів, буде запущено нові вибори.",
        reply_markup=no_confidence_confirm_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(NoConfidenceVote.waiting_confirm)
    await callback.answer()

@router.callback_query(NoConfidenceVote.waiting_confirm, F.data == "no_confidence_confirm_yes")
async def no_confidence_confirm_yes(callback: CallbackQuery, state: FSMContext, db, bot, pool):
    try:
        success, result = await start_no_confidence(callback.from_user.id, pool)
        if not success:
            await callback.message.edit_text(f"❌ {result}")
            await state.clear()
            await callback.answer()
            return

        # Надіслати оголошення в групу
        await bot.send_message(
            settings.GROUP_CHAT_ID,
            "🚫 <b>Розпочато вотум недовіри!</b>\n\n"
            "Голосування триватиме 24 години.\n"
            "Перейдіть у бот і натисніть 🗳️ Вибори → 🚫 Вотум недовіри, щоб проголосувати.",
            parse_mode="HTML"
        )

        await callback.message.edit_text("✅ Вотум недовіри запущено! Голосування триватиме 24 години.")
        await state.clear()
    except Exception as e:
        await callback.answer(f"Помилка: {e}", show_alert=True)

@router.callback_query(NoConfidenceVote.waiting_confirm, F.data == "no_confidence_confirm_no")
async def no_confidence_confirm_no(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Ініціацію вотуму скасовано.")
    await callback.answer()

# ========== СКЛАДАННЯ ПОВНОВАЖЕНЬ ==========

@router.callback_query(F.data == "resign_starosta")
async def resign_starosta_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 <b>Скласти повноваження старости</b>\n\n"
        "Ви впевнені? Будуть негайно запущені нові вибори.",
        reply_markup=resign_confirm_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(ResignStarosta.waiting_confirm)
    await callback.answer()

@router.callback_query(ResignStarosta.waiting_confirm, F.data == "resign_confirm_yes")
async def resign_starosta_yes(callback: CallbackQuery, state: FSMContext, pool):
    try:
        success, result = await start_regular_election(pool, callback.from_user.id)
        if success:
            await callback.message.edit_text("✅ Повноваження складено. Запущено нові вибори!")
        else:
            await callback.message.edit_text(f"❌ {result}")
        await state.clear()
    except Exception as e:
        await callback.answer(f"Помилка: {e}", show_alert=True)
    await callback.answer()

@router.callback_query(ResignStarosta.waiting_confirm, F.data == "resign_confirm_no")
async def resign_starosta_no(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Скасовано.")
    await callback.answer()
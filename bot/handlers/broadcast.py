# Масова розсилка

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline.common import confirm_cancel_keyboard, back_to_main_menu_btn
from bot.states.fsm import Broadcast
from services.broadcast_queue import broadcast_queue, BroadcastTask
from db.queries.students import get_active_students_telegram_ids
import html

router = Router()

@router.callback_query(F.data == "broadcast_start")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введіть текст повідомлення для розсилки (до 4000 символів):"
    )
    await state.set_state(Broadcast.waiting_text)
    await callback.answer()

@router.message(Broadcast.waiting_text)
async def broadcast_text_received(message: Message, state: FSMContext):
    text = message.text
    if len(text) > 4000:
        await message.answer("❌ Текст занадто довгий. Скоротіть до 4000 символів.")
        return
    await state.update_data(text=text)
    preview = f"Прев'ю повідомлення:\n─────────────────────\n{html.escape(text)}\n─────────────────────"
    await message.answer(preview, reply_markup=confirm_cancel_keyboard())
    await state.set_state(Broadcast.waiting_confirm)

@router.callback_query(Broadcast.waiting_confirm, F.data == "confirm_yes")
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext, db, student):
    data = await state.get_data()
    text = data["text"]
    await state.clear()

    # Отримати список отримувачів
    recipients = await get_active_students_telegram_ids(db)
    if not recipients:
        await callback.message.edit_text("Немає активних учнів з Telegram ID.")
        return

    task = BroadcastTask(
        sender_id=callback.from_user.id,
        chat_ids=recipients,
        text=text
    )
    await broadcast_queue.put(task)

    await callback.message.edit_text(
        "✅ Розсилку запущено. Результат отримаєте після завершення.",
        reply_markup=back_to_main_menu_btn()
    )
    await callback.answer()

@router.callback_query(Broadcast.waiting_confirm, F.data == "confirm_no")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Розсилку скасовано.")
    await callback.answer()
# Назва класу

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from bot.states.fsm import EditClassName
from db.queries.class_info import get_class_info, update_class_info

router = Router()

@router.callback_query(F.data == "admin_class_info")
async def edit_class_info_start(callback: CallbackQuery, state: FSMContext):
    info = await get_class_info(callback.bot["db_pool"])
    await callback.message.edit_text(f"Поточна назва: {info['class_number']}-{info['class_letter']}\nВведіть новий номер класу (1–11):")
    await state.set_state(EditClassName.waiting_number)
    await callback.answer()
# Редагування ДЗ

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline.admin import homework_management_keyboard
from bot.states.fsm import AddHomework, EditHomework
from db.queries.subjects import get_all_subjects
from db.queries.homework import add_homework, update_homework, soft_delete_homework, get_upcoming_homework
from services.schedule import parse_date_input

router = Router()

@router.callback_query(F.data == "admin_homework")
async def admin_homework_menu(callback: CallbackQuery):
    await callback.message.edit_text("Редагування ДЗ:", reply_markup=homework_management_keyboard())
    await callback.answer()

@router.callback_query(F.data == "hw_add")
async def add_homework_start(callback: CallbackQuery, state: FSMContext, db):
    subjects = await get_all_subjects(db)
    from bot.keyboards.inline.common import subjects_keyboard
    await callback.message.edit_text("Оберіть предмет:", reply_markup=subjects_keyboard(subjects))
    await state.set_state(AddHomework.waiting_subject)
    await callback.answer()

# Далі FSM кроки для додавання ДЗ...
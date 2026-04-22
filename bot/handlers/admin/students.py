# Керування класом

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline.admin import students_management_keyboard, role_keyboard, group_keyboard
from bot.states.fsm import AddStudent
from db.queries.students import create_student, update_student, deactivate_student, get_student_by_id
import html

router = Router()

@router.callback_query(F.data == "admin_students")
async def manage_students(callback: CallbackQuery, db):
    students = await get_all_active_students(db)
    text = "Список учнів:\n" + "\n".join(f"{s['id']}. {html.escape(s['full_name'])} ({s['role']})" for s in students)
    await callback.message.edit_text(text, reply_markup=students_management_keyboard())
    await callback.answer()

@router.callback_query(F.data == "student_add")
async def add_student_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введіть ПІБ учня:")
    await state.set_state(AddStudent.waiting_name)
    await callback.answer()

# Далі FSM для додавання учня...
import html
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from db.queries.students import get_student_by_telegram_id
from bot.keyboards.main_menu import get_main_menu_keyboard
from config import settings
from services.notifications import notify_admins_throttled

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, db, redis, student=None):
    await state.clear()
    user_id = message.from_user.id
    if student:
        role = student.get('role', 'student')
        class_text = f" учням {html.escape(student.get('class_name', ''))} класу" if student.get('class_name') else ""
        
        await message.answer(
            f"👋 Вітаємо, {html.escape(student['full_name'])}!\n"
            f"Я ClassHelperProBot. Моя місія — допомога{class_text}.\n"
            f"Оберіть дію з меню нижче.",
            reply_markup=get_main_menu_keyboard(
                is_super_admin=(user_id in settings.super_admin_ids_set),
                role=role
            )
        )
    else:
        await message.answer(
            f"❌ Вас ще немає в списку класу.\n"
            f"Зверніться до старости або адміністратора, щоб вас додали.\n\n"
            f"Ваш Telegram ID: {user_id}\n"
            f"(скопіюйте та передайте адміністратору)"
        )
        await notify_admins_throttled(
            redis, user_id,
            f"🔔 Новий користувач намагався запустити бота:\n"
            f"Ім'я: {html.escape(message.from_user.full_name)}\n"
            f"Username: @{message.from_user.username or 'немає'}\n"
            f"Telegram ID: {user_id}\n\n"
            f"Якщо це учень класу — додайте його через адмін-панель:\n"
            f"/admin → Керування класом → Змінити дані учня → Встановити Telegram ID"
        )

@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(
        f"🆔 Ваш Telegram ID: {message.from_user.id}\n"
        f"Скопіюйте його та передайте адміністратору для реєстрації в системі."
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, student):
    if not student:
        await callback.answer("Спочатку зареєструйтесь через /start.", show_alert=True)
        return
    role = student.get('role', 'student')
    user_id = callback.from_user.id
    class_text = f" учням {html.escape(student.get('class_name', ''))} класу" if student.get('class_name') else ""
    
    await callback.message.answer(
        f"👋 Вітаємо, {html.escape(student['full_name'])}!\n"
        f"Я ClassHelperProBot. Моя місія — допомога{class_text}.\n"
        f"Оберіть дію з меню нижче.",
        reply_markup=get_main_menu_keyboard(
            is_super_admin=(user_id in settings.super_admin_ids_set),
            role=role
        )
    )
    await callback.answer()
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.states.fsm import WriteDeveloper
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.inline.common import cancel_button
from config import settings
from services.notifications import notify_admins

router = Router()

@router.callback_query(F.data == "admin_instruction")
async def admin_instruction(callback: CallbackQuery):
    text = (
        "📖 <b>Детальна інструкція адмін-панелі</b>\n\n"
        "• <b>🩺 Відмітити відсутніх сьогодні</b> — список учнів з кнопками ✅/❌. Натискання миттєво змінює статус.\n"
        "• <b>📊 Відсутні за 5 днів</b> — звіт за останні 5 днів.\n"
        "• <b>📝 Редагувати ДЗ</b> — додавання, зміна, видалення домашніх завдань.\n"
        "   - Додати: вибір предмету → текст → тип → автодата → підтвердження.\n"
        "   - Змінити: список ДЗ з кнопками ✏️/🗑. Можна редагувати текст або видалити.\n"
        "• <b>👥 Керування класом</b> — додавання нового учня (ПІБ, роль, підгрупа, Telegram ID).\n"
        "• <b>🔄 Скинути борги чергувань</b> — скидання пропусків.\n"
        "• <b>🗓 Канікули</b> — додавання/видалення канікулярних періодів.\n"
        "• <b>🏷 Редагувати назву класу</b> — зміна номера та літери класу.\n"
        "• <b>🗳️ Керування виборами</b> — ручне призначення виборів, призначення старости, історія.\n"
        "• <b>📖 Детальна інструкція</b> — ця довідка.\n"
        "• <b>✉️ Написати розробнику</b> — відправити повідомлення власнику бота."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Написати розробнику", callback_data="write_developer")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "write_developer")
async def write_developer_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✉️ <b>Написати розробнику</b>\n\n"
        "Введіть ваше повідомлення. Воно буде переслано власнику бота.",
        reply_markup=cancel_button(),
        parse_mode="HTML"
    )
    await state.set_state(WriteDeveloper.waiting_message)
    await callback.answer()

@router.message(WriteDeveloper.waiting_message)
async def process_developer_message(message: Message, state: FSMContext):
    text = message.text
    user = message.from_user
    
    # Надіслати повідомлення всім суперадмінам
    await notify_admins(
        f"✉️ <b>Повідомлення від користувача</b>\n\n"
        f"Від: {user.full_name} (@{user.username or 'немає'})\n"
        f"ID: {user.id}\n\n"
        f"<b>Текст:</b>\n{text}"
    )
    
    await state.clear()
    await message.answer(
        "✅ Ваше повідомлення надіслано розробнику. Дякуємо!",
        reply_markup=get_main_menu_keyboard(
            is_super_admin=(user.id in settings.super_admin_ids_set)
        )
    )
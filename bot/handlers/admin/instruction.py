from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

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
async def write_developer(callback: CallbackQuery, state, redis):
    # Тут можна переключити в FSM для прийому повідомлення
    await callback.message.answer("Функціонал у розробці. Повідомлення буде надіслано адміністратору.")
    await callback.answer()
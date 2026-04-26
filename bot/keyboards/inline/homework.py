from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def homework_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 На сьогодні", callback_data="hw_today")],
        [InlineKeyboardButton(text="📅 На 3 дні", callback_data="hw_3_days")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
    ])
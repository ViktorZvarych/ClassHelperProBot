from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def homework_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 На завтра", callback_data="hw_tomorrow")],
        [InlineKeyboardButton(text="📅 На після-завтра", callback_data="hw_day_after")],
        [InlineKeyboardButton(text="🗓 На дату", callback_data="hw_by_date")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
    ])

back_to_homework_menu_btn = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Назад до ДЗ", callback_data="homework_menu")]
])
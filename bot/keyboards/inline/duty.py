from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def duty_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📆 Чергові на сьогодні", callback_data="duty_today")],
        [InlineKeyboardButton(text="📅 Чергові на завтра", callback_data="duty_tomorrow")],
        [InlineKeyboardButton(text="🗓 Історія за 5 днів", callback_data="duty_history")],
        [InlineKeyboardButton(text="✅ Відмітити чергування", callback_data="duty_confirm")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
    ])

def duty_confirm_keyboard(student_id: int, date_str: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити", callback_data=f"duty_confirm_{student_id}")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="duty_cancel")]
    ])
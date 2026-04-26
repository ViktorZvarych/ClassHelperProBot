from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def confirm_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити", callback_data="confirm_yes"),
         InlineKeyboardButton(text="❌ Скасувати", callback_data="confirm_no")]
    ])

def cancel_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_action")]
    ])

def back_to_main_menu_btn():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="back_to_main")]
    ])

def broadcast_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Надіслати повідомлення класу", callback_data="broadcast_start")]
    ])

def subjects_keyboard(subjects):
    """Клавіатура зі списком предметів."""
    buttons = []
    for subj in subjects:
        buttons.append([InlineKeyboardButton(text=subj["name"], callback_data=f"subj_{subj['id']}")])
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def homework_type_keyboard():
    """Вибір типу ДЗ (контрольна/звичайне)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚨 Контрольна робота", callback_data="hw_control")],
        [InlineKeyboardButton(text="📝 Звичайне ДЗ", callback_data="hw_regular")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
    ])
    
def back_to_admin_btn():
    """Кнопка повернення до адмін-панелі."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад до адмін-панелі", callback_data="admin_back")]
    ])
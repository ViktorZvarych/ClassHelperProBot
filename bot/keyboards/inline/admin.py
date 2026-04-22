from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🩺 Відмітити відсутніх сьогодні", callback_data="admin_absence")],
        [InlineKeyboardButton(text="📝 Редагувати ДЗ", callback_data="admin_homework")],
        [InlineKeyboardButton(text="👥 Керування класом", callback_data="admin_students")],
        [InlineKeyboardButton(text="🔄 Скинути борги чергувань", callback_data="admin_reset_skip")],
        [InlineKeyboardButton(text="🗓 Канікули", callback_data="admin_holidays")],
        [InlineKeyboardButton(text="🏷 Редагувати назву класу", callback_data="admin_class_info")],
        [InlineKeyboardButton(text="↩️ Назад до головного меню", callback_data="back_to_main")]
    ])

def homework_management_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Додати ДЗ", callback_data="hw_add")],
        [InlineKeyboardButton(text="✏️ Змінити ДЗ", callback_data="hw_edit")],
        [InlineKeyboardButton(text="🗑 Видалити ДЗ", callback_data="hw_delete")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
    ])

def students_management_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Додати учня", callback_data="student_add")],
        [InlineKeyboardButton(text="✏️ Змінити дані", callback_data="student_edit")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
    ])

def holidays_management_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Додати канікули", callback_data="holiday_add")],
        [InlineKeyboardButton(text="🗑 Видалити канікули", callback_data="holiday_delete")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
    ])

def absence_students_keyboard(students, statuses):
    buttons = []
    for s in students:
        absent = statuses.get(s["id"], False)
        emoji = "❌" if absent else "✅"
        buttons.append([InlineKeyboardButton(text=f"{emoji} {s['full_name']}", callback_data=f"toggle_absence_{s['id']}")])
    buttons.append([InlineKeyboardButton(text="✅ Зберегти зміни", callback_data="absence_save")])
    buttons.append([InlineKeyboardButton(text="❌ Скасувати", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
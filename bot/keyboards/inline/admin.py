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
    row = []
    for s in students:
        absent = statuses.get(s["id"], False)
        emoji = "❌" if absent else "✅"
        # Коротке ім'я (прізвище + перша літера імені)
        name_parts = s["full_name"].split()
        if len(name_parts) >= 2:
            short_name = f"{name_parts[0]} {name_parts[1][0]}."
        else:
            short_name = s["full_name"]
        
        row.append(InlineKeyboardButton(
            text=f"{emoji} {short_name}",
            callback_data=f"toggle_absence_{s['id']}"
        ))
        
        # По дві кнопки в рядок
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    # Додаємо останню кнопку, якщо вона одна в рядку
    if row:
        buttons.append(row)
    
    # Кнопка "Назад"
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="absence_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_admin_btn():
    """Кнопка повернення до адмін-панелі."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад до адмін-панелі", callback_data="admin_back")]
    ])
    
def role_keyboard():
    """Клавіатура вибору ролі учня."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Учень", callback_data="role_student")],
        [InlineKeyboardButton(text="📎 Заст. старости", callback_data="role_zamstarosta")],
        [InlineKeyboardButton(text="✏️ Редактор", callback_data="role_redactor")],
        [InlineKeyboardButton(text="🎓 Староста", callback_data="role_starosta")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
    ])

def group_keyboard():
    """Клавіатура вибору підгрупи."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🅰️ Група A", callback_data="group_A")],
        [InlineKeyboardButton(text="🅱️ Група B", callback_data="group_B")],
        [InlineKeyboardButton(text="👥 Без підгрупи", callback_data="group_all")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
    ])
    
def confirm_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити", callback_data="confirm_yes"),
         InlineKeyboardButton(text="❌ Скасувати", callback_data="confirm_no")]
    ])
import calendar
from datetime import date
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
    
def calendar_keyboard(year: int, month: int, prefix: str = "cal") -> InlineKeyboardMarkup:
    """Генерує клавіатуру календаря на вказаний місяць."""
    kb = []
    # Рядок із назвою місяця та роком + кнопки навігації
    month_name = [
        "Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
        "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"
    ][month - 1]
    nav_row = [
        InlineKeyboardButton(text="◀️", callback_data=f"{prefix}_prev_{year}_{month}"),
        InlineKeyboardButton(text=f"{month_name} {year}", callback_data="ignore"),
        InlineKeyboardButton(text="▶️", callback_data=f"{prefix}_next_{year}_{month}")
    ]
    kb.append(nav_row)

    # Рядок із днями тижня
    days_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
    kb.append([InlineKeyboardButton(text=dn, callback_data="ignore") for dn in days_names])

    # Дні місяця
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                row.append(InlineKeyboardButton(
                    text=str(day),
                    callback_data=f"{prefix}_day_{year}_{month}_{day}"
                ))
        kb.append(row)

    # Рядок із кнопкою скасування
    kb.append([InlineKeyboardButton(text="❌ Скасувати", callback_data=f"{prefix}_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)
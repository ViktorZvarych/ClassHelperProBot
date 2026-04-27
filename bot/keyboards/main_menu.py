from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard(is_super_admin: bool = False, role: str = 'student') -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📅 Розклад сьогодні"), KeyboardButton(text="📆 Розклад на 3 дні")],
        [KeyboardButton(text="📖 ДЗ на сьогодні"), KeyboardButton(text="📚 ДЗ на 3 дні")],
        [KeyboardButton(text="🧹 Чергування"), KeyboardButton(text="👥 Список учнів")],
    ]
    if is_super_admin:
        buttons.append([KeyboardButton(text="⚙️ Адмін-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, persistent=True)
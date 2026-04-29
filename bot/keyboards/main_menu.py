from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard(is_super_admin: bool = False, role: str = 'student') -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📅 Розклад"), KeyboardButton(text="📚 Домашнє завдання")],
        [KeyboardButton(text="🧹 Чергування"), KeyboardButton(text="👥 Список учнів")],
        [KeyboardButton(text="🗳️ Вибори"), KeyboardButton(text="📖 Інструкція")],
    ]
    if is_super_admin:
        buttons.append([KeyboardButton(text="⚙️ Адмін-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, persistent=True)
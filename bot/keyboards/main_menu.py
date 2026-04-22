# Reply-клавіатура головного меню

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard(is_super_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📅 Розклад сьогодні"), KeyboardButton(text="📆 Розклад завтра")],
        [KeyboardButton(text="📚 Домашнє завдання"), KeyboardButton(text="🧹 Чергування")],
        [KeyboardButton(text="👥 Список учнів"), KeyboardButton(text="📋 Відсутні за 5 днів")],
    ]
    if is_super_admin:
        buttons.append([KeyboardButton(text="⚙️ Адмін-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, persistent=True)
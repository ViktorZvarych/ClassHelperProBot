# Обробка невідомих команд/повідомлень

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_main_menu_keyboard
from db.queries.students import get_students_list_with_debt
from db.queries.absence import get_absence_last_5_days
from config import settings
import html

router = Router()

@router.message(F.text == "👥 Список учнів")
async def list_students(message: Message, db, student, is_super_admin):
    
    students = await get_students_list_with_debt(db)
    if not students:
        await message.answer("Список учнів порожній.")
        return
    text = f"👥 Список учнів:\n\n"
    for i, s in enumerate(students, 1):
        role_icon = {"starosta": "🎓 Староста", "zamstarosta": "📎 Заст. старости", "redactor": "✏️ Редактор"}.get(s["role"], "")
        debt = "ТАК ❗" if s["consecutive_duty_skip"] > 0 else "НІ ✅"
        line = f"{i}. {html.escape(s['full_name'])}"
        if role_icon:
            line += f" ({role_icon})"
        line += f" — борг: {debt}"
        text += line + "\n"
    text += f"\nВсього учнів: {len(students)}"
    await message.answer(text)
    # Додати кнопку розсилки для уповноважених
    if is_super_admin or student and student["role"] in ("starosta", "guest"):
        from bot.keyboards.inline.common import broadcast_button
        await message.answer("✉️", reply_markup=broadcast_button())

@router.message(F.text == "📋 Відсутні за 5 днів")
async def absent_last_5_days(message: Message, db):
    records = await get_absence_last_5_days(db)
    if not records:
        await message.answer("📭 За останні 5 днів відсутніх не зафіксовано.")
        return
    text = "📊 Відсутні за останні 5 днів:\n\n"
    for day_str, names in records.items():
        if names:
            text += f"🔹 {day_str}: {', '.join(html.escape(n) for n in names)}\n"
        else:
            text += f"🔹 {day_str}: немає\n"
    await message.answer(text)
    
@router.message(F.text == "📖 Інструкція")
async def show_instructions(message: Message):
    text = (
        "📖 <b>Головне меню бота</b>\n\n"
        "• <b>📅 Розклад сьогодні</b> — уроки на поточний день\n"
        "• <b>📆 Розклад на 3 дні</b> — уроки на завтра + 2 дні\n"
        "• <b>📖 ДЗ на сьогодні</b> — домашнє завдання на сьогодні\n"
        "• <b>📚 ДЗ на 3 дні</b> — ДЗ на завтра, післязавтра і післяпіслязавтра\n"
        "• <b>🧹 Чергування</b> — список чергових, історія, відмітка виконання\n"
        "• <b>👥 Список учнів</b> — список класу, ролі, борги (староста може розсилати повідомлення)\n"
        "• <b>🗳️ Вибори</b> — інформація про актив класу, вотум недовіри, складання повноважень\n"
        "• <b>📖 Інструкція</b> — цей опис\n"
        "• <b>⚙️ Адмін-панель</b> (тільки для адміністраторів) — керування даними учнів, ДЗ, канікулами, виборами\n\n"
        "Для початку роботи натисніть /start"
    )
    await message.answer(text, parse_mode="HTML")

@router.message()
async def unknown_message(message: Message, state: FSMContext, student):
    # Відповідь на невідомі команди/текст поза FSM
    await message.answer(
        "Я не розумію цю команду. Скористайтеся меню нижче 👇",
        reply_markup=get_main_menu_keyboard(is_super_admin=(message.from_user.id in settings.super_admin_ids_set))
    )
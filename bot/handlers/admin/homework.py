import html
from datetime import date, datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from bot.keyboards.inline.admin import homework_management_keyboard, confirm_cancel_keyboard
from bot.keyboards.inline.common import subjects_keyboard, cancel_button, back_to_admin_btn, homework_type_keyboard
from bot.states.fsm import AddHomework, EditHomework
from db.queries.subjects import get_all_subjects
from db.queries.homework import add_homework, get_upcoming_homework, soft_delete_homework, update_homework
from services.schedule import find_next_date_for_subject
from config import settings

router = Router()

# ============== ГОЛОВНЕ МЕНЮ ДЗ ==============
@router.callback_query(F.data == "admin_homework")
async def admin_homework_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Редагування ДЗ:",
        reply_markup=homework_management_keyboard()
    )
    await callback.answer()

# ============== ДОДАВАННЯ ДЗ ==============
@router.callback_query(F.data == "hw_add")
async def add_homework_start(callback: CallbackQuery, state: FSMContext, db):
    subjects = await get_all_subjects(db)
    if not subjects:
        await callback.message.edit_text("Список предметів порожній.", reply_markup=back_to_admin_btn())
        await callback.answer()
        return
    await callback.message.edit_text(
        "Оберіть предмет:",
        reply_markup=subjects_keyboard(subjects)
    )
    await state.set_state(AddHomework.waiting_subject)
    await callback.answer()

@router.callback_query(AddHomework.waiting_subject, F.data.startswith("subj_"))
async def process_subject(callback: CallbackQuery, state: FSMContext):
    subject_id = int(callback.data.split("_")[1])
    await state.update_data(subject_id=subject_id)
    await callback.message.edit_text(
        "Введіть текст домашнього завдання (до 500 символів):",
        reply_markup=cancel_button()
    )
    await state.set_state(AddHomework.waiting_text)
    await callback.answer()

@router.message(AddHomework.waiting_text)
async def process_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text) > 500:
        await message.answer("❌ Текст занадто довгий. Скоротіть до 500 символів.")
        return
    await state.update_data(description=text)
    await message.answer(
        "Оберіть тип завдання:",
        reply_markup=homework_type_keyboard()
    )
    await state.set_state(AddHomework.waiting_is_control)

@router.callback_query(AddHomework.waiting_is_control, F.data.in_({"hw_control", "hw_regular"}))
async def process_type(callback: CallbackQuery, state: FSMContext, db, redis):
    is_control = (callback.data == "hw_control")
    await state.update_data(is_control=is_control)
    data = await state.get_data()
    subject_id = data["subject_id"]

    today = datetime.now().date()
    next_date = await find_next_date_for_subject(subject_id, today, db, redis)
    if next_date is None:
        await callback.message.edit_text(
            "❌ Цей предмет не знайдено в розкладі на найближчі 60 днів. Перевірте розклад.",
            reply_markup=homework_management_keyboard()
        )
        await state.clear()
        await callback.answer()
        return

    await state.update_data(due_date=next_date)

    subject_name = await _get_subject_name(db, subject_id)
    control_text = "🚨 Контрольна" if is_control else "📝 Звичайне"
    preview = (
        f"📚 Нове домашнє завдання:\n"
        f"Предмет: {html.escape(subject_name)}\n"
        f"Дата: {next_date.strftime('%d.%m.%Y')}\n"
        f"Тип: {control_text}\n"
        f"Текст: {html.escape(data['description'])}\n\n"
        f"Підтвердити?"
    )
    await callback.message.edit_text(preview, reply_markup=confirm_cancel_keyboard())
    await state.set_state(AddHomework.waiting_confirm)
    await callback.answer()

@router.callback_query(AddHomework.waiting_confirm, F.data == "confirm_yes")
async def confirm_add(callback: CallbackQuery, state: FSMContext, db):
    data = await state.get_data()
    await add_homework(
        db,
        subject_id=data["subject_id"],
        due_date=data["due_date"],
        description=data["description"],
        is_control=data["is_control"],
        added_by=callback.from_user.id
    )
    await state.clear()
    await callback.message.edit_text(
        "✅ Домашнє завдання додано!",
        reply_markup=homework_management_keyboard()
    )
    await callback.answer()

@router.callback_query(AddHomework.waiting_confirm, F.data == "confirm_no")
async def cancel_add(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Додавання скасовано.",
        reply_markup=homework_management_keyboard()
    )
    await callback.answer()

# ============== РЕДАГУВАННЯ ДЗ (ПЕРЕГЛЯД СПИСКУ) ==============
@router.callback_query(F.data == "hw_edit")
async def edit_homework_list(callback: CallbackQuery, db):
    hw_list = await get_upcoming_homework(db, limit=50)
    if not hw_list:
        await callback.message.edit_text(
            "📭 Немає домашніх завдань для редагування.",
            reply_markup=homework_management_keyboard()
        )
        await callback.answer()
        return

    text = "📝 Список домашніх завдань:"
    kb = []
    for i, hw in enumerate(hw_list):
        date_str = hw["due_date"].strftime("%d.%m")
        control_mark = "🚨 " if hw["is_control"] else ""
        desc_short = hw["description"][:50] + "..." if len(hw["description"]) > 50 else hw["description"]
        
        row_text = f"{date_str} | {control_mark}{hw['subject_name']}: {desc_short}"
        
        # Основний текст на всю ширину
        kb.append([InlineKeyboardButton(text=row_text, callback_data=f"hw_info_{hw['id']}")])
        # Іконки окремим рядком
        kb.append([
            InlineKeyboardButton(text="✏️ Редагувати", callback_data=f"hw_edit_text_{hw['id']}"),
            InlineKeyboardButton(text="🗑 Видалити", callback_data=f"hw_delete_{hw['id']}")
        ])
        # Пустий рядок-роздільник між предметами (крім останнього)
        if i < len(hw_list) - 1:
            kb.append([InlineKeyboardButton(text=" ", callback_data="empty")])
    
    kb.append([InlineKeyboardButton(text="↩️ Назад", callback_data="admin_homework")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await callback.answer()

# Додайте обробник для порожньої кнопки (щоб не було помилок)
@router.callback_query(F.data == "empty")
async def empty_callback(callback: CallbackQuery):
    await callback.answer()

# ============== ІНФО ПРО ДЗ ==============
@router.callback_query(F.data.startswith("hw_info_"))
async def hw_info(callback: CallbackQuery, db):
    hw_id = int(callback.data.split("_")[2])
    row = await db.fetchrow("""
        SELECT h.description, h.is_control, h.due_date, s.name AS subject_name
        FROM homework h
        JOIN subjects s ON h.subject_id = s.id
        WHERE h.id = $1
    """, hw_id)
    if not row:
        await callback.answer("❌ Запис не знайдено.")
        return

    control_text = "🚨 Контрольна" if row["is_control"] else "📝 Звичайне"
    text = (
        f"📚 <b>Домашнє завдання:</b>\n\n"
        f"📅 {row['due_date'].strftime('%d.%m.%Y')} | {html.escape(row['subject_name'])}\n"
        f"🏷 {control_text}\n"
        f"📝 {html.escape(row['description'])}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Змінити текст", callback_data=f"hw_edit_text_{hw_id}"),
         InlineKeyboardButton(text="🗑 Видалити", callback_data=f"hw_delete_{hw_id}")],
        [InlineKeyboardButton(text="↩️ Назад до списку", callback_data="hw_edit")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# ============== ВИДАЛЕННЯ ДЗ ==============
@router.callback_query(F.data.startswith("hw_delete_"))
async def delete_hw(callback: CallbackQuery, db):
    hw_id = int(callback.data.split("_")[2])
    row = await db.fetchrow("""
        SELECT h.description, h.due_date, s.name AS subject_name
        FROM homework h
        JOIN subjects s ON h.subject_id = s.id
        WHERE h.id = $1
    """, hw_id)
    if not row:
        await callback.answer("❌ Запис не знайдено.")
        return

    await callback.message.edit_text(
        f"⚠️ <b>Видалити ДЗ?</b>\n\n"
        f"📅 {row['due_date'].strftime('%d.%m.%Y')} | {html.escape(row['subject_name'])}\n"
        f"📝 {html.escape(row['description'])}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Так, видалити", callback_data=f"hw_delete_confirm_{hw_id}"),
             InlineKeyboardButton(text="❌ Скасувати", callback_data="hw_edit")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("hw_delete_confirm_"))
async def delete_hw_confirm(callback: CallbackQuery, db):
    hw_id = int(callback.data.split("_")[3])
    await soft_delete_homework(db, [hw_id])
    await edit_homework_list(callback, db)
    await callback.answer("✅ Видалено!")

# ============== РЕДАГУВАННЯ ТЕКСТУ ДЗ ==============
@router.callback_query(F.data.startswith("hw_edit_text_"))
async def edit_text_start(callback: CallbackQuery, state: FSMContext, db):
    hw_id = int(callback.data.split("_")[3])
    row = await db.fetchrow("""
        SELECT h.description, h.due_date, s.name AS subject_name
        FROM homework h
        JOIN subjects s ON h.subject_id = s.id
        WHERE h.id = $1
    """, hw_id)
    if not row:
        await callback.answer("❌ Запис не знайдено.")
        return

    await state.update_data(edit_hw_id=hw_id)
    await callback.message.edit_text(
        f"✏️ <b>Редагування ДЗ:</b>\n\n"
        f"📅 {row['due_date'].strftime('%d.%m.%Y')} | {html.escape(row['subject_name'])}\n\n"
        f"<b>Поточний текст:</b>\n"
        f"<code>{html.escape(row['description'])}</code>\n\n"
        f"<i>👆 Натисніть на текст вище, щоб скопіювати його,</i>\n"
        f"<i>потім вставте у поле введення та відредагуйте:</i>",
        reply_markup=cancel_button(),
        parse_mode="HTML"
    )
    await state.set_state(EditHomework.waiting_new_value)
    await callback.answer()

@router.message(EditHomework.waiting_new_value)
async def edit_text_done(message: Message, state: FSMContext, db):
    new_text = message.text.strip()
    if len(new_text) > 500:
        await message.answer("❌ Текст занадто довгий. Скоротіть до 500 символів.")
        return
    data = await state.get_data()
    hw_id = data["edit_hw_id"]
    await update_homework(db, hw_id, description=new_text)
    await state.clear()
    await message.answer(
        "✅ Текст домашнього завдання оновлено!",
        reply_markup=homework_management_keyboard()
    )

# ============== ДОПОМІЖНА ФУНКЦІЯ ==============
async def _get_subject_name(db, subject_id):
    row = await db.fetchrow("SELECT name FROM subjects WHERE id=$1", subject_id)
    return row["name"] if row else "Невідомий предмет"
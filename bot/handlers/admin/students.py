import html
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline.admin import students_management_keyboard, role_keyboard, group_keyboard, confirm_cancel_keyboard, back_to_admin_btn
from bot.keyboards.inline.common import cancel_button
from bot.states.fsm import AddStudent
from db.queries.students import get_all_active_students, create_student, update_student, deactivate_student, get_student_by_id

router = Router()

@router.callback_query(F.data == "admin_students")
async def manage_students(callback: CallbackQuery, db):
    students = await get_all_active_students(db)  # гості не видно
    if not students:
        text = "👥 Список учнів порожній."
    else:
        text = "👥 <b>Список учнів:</b>\n\n"
        for s in students:
            role_map = {
                "student": "👤",
                "starosta": "🎓",
                "zamstarosta": "📎",
                "guest": "👥"
            }
            role_icon = role_map.get(s["role"], "👤")
            tg = f" | TG: {s['telegram_id']}" if s["telegram_id"] else ""
            text += f"{s['id']}. {role_icon} {html.escape(s['full_name'])} ({s['role']}){tg}\n"
    await callback.message.edit_text(text, reply_markup=students_management_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "student_add")
async def add_student_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➕ <b>Додавання нового користувача</b>\n\nВведіть ПІБ:",
        reply_markup=cancel_button(), parse_mode="HTML"
    )
    await state.set_state(AddStudent.waiting_name)
    await callback.answer()

@router.message(AddStudent.waiting_name)
async def process_student_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 100:
        await message.answer("❌ ПІБ має містити від 2 до 100 символів. Введіть ще раз:")
        return
    await state.update_data(full_name=name)
    await message.answer("Оберіть роль:", reply_markup=role_keyboard())
    await state.set_state(AddStudent.waiting_role)

@router.callback_query(AddStudent.waiting_role, F.data.startswith("role_"))
async def process_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split("_")[1]
    await state.update_data(role=role)
    if role == "guest":
        # Гостю не потрібна підгрупа
        await state.update_data(group_name="all")
        await callback.message.edit_text(
            "Введіть Telegram ID користувача\n(або /skip для пропуску):",
            reply_markup=cancel_button()
        )
        await state.set_state(AddStudent.waiting_telegram_id)
    else:
        await callback.message.edit_text("Оберіть підгрупу:", reply_markup=group_keyboard())
        await state.set_state(AddStudent.waiting_group)
    await callback.answer()

@router.callback_query(AddStudent.waiting_group, F.data.startswith("group_"))
async def process_group(callback: CallbackQuery, state: FSMContext):
    group = callback.data.split("_")[1].upper()
    if group == "ALL":
        group = "all"
    await state.update_data(group_name=group)
    await callback.message.edit_text(
        "Введіть Telegram ID учня\n(або /skip для пропуску):",
        reply_markup=cancel_button()
    )
    await state.set_state(AddStudent.waiting_telegram_id)
    await callback.answer()

@router.message(AddStudent.waiting_telegram_id)
async def process_telegram_id(message: Message, state: FSMContext, db):
    text = message.text.strip()
    if text.lower() == "/skip":
        telegram_id = None
    else:
        try:
            telegram_id = int(text)
        except ValueError:
            await message.answer("❌ Введіть числовий Telegram ID або /skip:")
            return

    await state.update_data(telegram_id=telegram_id)
    data = await state.get_data()

    # Перевірка на дублювання старости (тільки для учнів)
    if data["role"] == "starosta":
        existing = await db.fetchval(
            "SELECT id FROM students WHERE role = 'starosta' AND is_active = true LIMIT 1"
        )
        if existing:
            await message.answer(
                "❌ Активний староста вже існує. Спочатку деактивуйте або змініть роль поточного старости.",
                reply_markup=students_management_keyboard()
            )
            await state.clear()
            return

    # Перевірка на дублювання telegram_id
    if telegram_id:
        existing = await db.fetchval(
            "SELECT id FROM students WHERE telegram_id = $1 AND id != $2",
            telegram_id, 0
        )
        if existing:
            await message.answer(
                "❌ Цей Telegram ID вже прив'язано до іншого користувача.",
                reply_markup=students_management_keyboard()
            )
            await state.clear()
            return

    # Підтвердження
    role_display = {
        "student": "👤 Учень",
        "starosta": "🎓 Староста",
        "zamstarosta": "📎 Заст. старости",
        "guest": "👥 Гість"
    }.get(data["role"], data["role"])
    group_display = {"all": "Без підгрупи", "A": "Група A", "B": "Група B"}.get(data["group_name"], data["group_name"])
    tg_display = str(telegram_id) if telegram_id else "—"

    await message.answer(
        f"➕ <b>Новий користувач:</b>\n\n"
        f"ПІБ: <b>{html.escape(data['full_name'])}</b>\n"
        f"Роль: <b>{role_display}</b>\n"
        f"Підгрупа: <b>{group_display}</b>\n"
        f"Telegram ID: <b>{tg_display}</b>\n\n"
        f"Підтвердити?",
        reply_markup=confirm_cancel_keyboard(), parse_mode="HTML"
    )
    await state.set_state(AddStudent.waiting_confirm)

@router.callback_query(AddStudent.waiting_confirm, F.data == "confirm_yes")
async def confirm_add_student(callback: CallbackQuery, state: FSMContext, db):
    data = await state.get_data()
    await create_student(
        db,
        full_name=data["full_name"],
        group_name=data["group_name"],
        role=data["role"],
        telegram_id=data.get("telegram_id")
    )
    await state.clear()
    await callback.message.edit_text(
        f"✅ Користувача <b>{html.escape(data['full_name'])}</b> додано!",
        reply_markup=students_management_keyboard(), parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(AddStudent.waiting_confirm, F.data == "confirm_no")
async def cancel_add_student(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Додавання скасовано.", reply_markup=students_management_keyboard())
    await callback.answer()

@router.callback_query(F.data == "students_back")
async def students_back(callback: CallbackQuery):
    from bot.keyboards.inline.admin import admin_panel_keyboard
    await callback.message.edit_text("Адміністративна панель:", reply_markup=admin_panel_keyboard())
    await callback.answer()
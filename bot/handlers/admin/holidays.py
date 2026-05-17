import html
from datetime import date, datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline.admin import holidays_management_keyboard, confirm_cancel_keyboard
from bot.keyboards.inline.common import calendar_keyboard, back_to_admin_btn
from bot.states.fsm import AddHoliday
from db.queries.holidays import get_all_holidays, add_holiday, delete_holiday

router = Router()

# ================== ГОЛОВНЕ МЕНЮ КАНІКУЛ ==================
@router.callback_query(F.data == "admin_holidays")
async def manage_holidays(callback: CallbackQuery, db):
    holidays = await get_all_holidays(db)
    if not holidays:
        text = "📭 Канікули не знайдено."
    else:
        text = "🗓 <b>Канікули:</b>\n\n"
        for h in holidays:
            start = h["start_date"].strftime("%d.%m.%Y")
            end = h["end_date"].strftime("%d.%m.%Y")
            desc = f" — {html.escape(h['description'])}" if h.get("description") else ""
            text += f"• {start} – {end}{desc}\n"
    await callback.message.edit_text(text, reply_markup=holidays_management_keyboard(), parse_mode="HTML")
    await callback.answer()

# ================== ДОДАВАННЯ КАНІКУЛ ==================
@router.callback_query(F.data == "holiday_add")
async def add_holiday_start(callback: CallbackQuery, state: FSMContext):
    today = date.today()
    await state.update_data(holiday_start_year=today.year, holiday_start_month=today.month)
    await callback.message.edit_text(
        "📅 <b>Оберіть початкову дату канікул:</b>",
        reply_markup=calendar_keyboard(today.year, today.month, prefix="holiday_start"),
        parse_mode="HTML"
    )
    await state.set_state(AddHoliday.waiting_start_date)
    await callback.answer()

# ---- Обробка навігації та вибору для ПОЧАТКОВОЇ дати ----
@router.callback_query(AddHoliday.waiting_start_date, F.data.startswith("holiday_start_prev_"))
async def holiday_start_prev(callback: CallbackQuery, state: FSMContext):
    _, _, y, m = callback.data.split("_")
    year, month = int(y), int(m)
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1
    await state.update_data(holiday_start_year=year, holiday_start_month=month)
    await callback.message.edit_reply_markup(reply_markup=calendar_keyboard(year, month, prefix="holiday_start"))
    await callback.answer()

@router.callback_query(AddHoliday.waiting_start_date, F.data.startswith("holiday_start_next_"))
async def holiday_start_next(callback: CallbackQuery, state: FSMContext):
    _, _, y, m = callback.data.split("_")
    year, month = int(y), int(m)
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    await state.update_data(holiday_start_year=year, holiday_start_month=month)
    await callback.message.edit_reply_markup(reply_markup=calendar_keyboard(year, month, prefix="holiday_start"))
    await callback.answer()

@router.callback_query(AddHoliday.waiting_start_date, F.data.startswith("holiday_start_day_"))
async def holiday_start_day_selected(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    year, month, day = int(parts[3]), int(parts[4]), int(parts[5])
    start_date = date(year, month, day)
    await state.update_data(start_date=start_date)

    # Переходимо до вибору кінцевої дати
    today = date.today()
    await state.update_data(holiday_end_year=year, holiday_end_month=month)  # стартовий місяць як у початкової
    await callback.message.edit_text(
        "📅 <b>Оберіть кінцеву дату канікул:</b>",
        reply_markup=calendar_keyboard(year, month, prefix="holiday_end"),
        parse_mode="HTML"
    )
    await state.set_state(AddHoliday.waiting_end_date)
    await callback.answer()

@router.callback_query(AddHoliday.waiting_start_date, F.data == "holiday_start_cancel")
async def holiday_start_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Додавання скасовано.", reply_markup=holidays_management_keyboard())
    await callback.answer()

# ---- Обробка навігації та вибору для КІНЦЕВОЇ дати ----
@router.callback_query(AddHoliday.waiting_end_date, F.data.startswith("holiday_end_prev_"))
async def holiday_end_prev(callback: CallbackQuery, state: FSMContext):
    _, _, y, m = callback.data.split("_")
    year, month = int(y), int(m)
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1
    await state.update_data(holiday_end_year=year, holiday_end_month=month)
    await callback.message.edit_reply_markup(reply_markup=calendar_keyboard(year, month, prefix="holiday_end"))
    await callback.answer()

@router.callback_query(AddHoliday.waiting_end_date, F.data.startswith("holiday_end_next_"))
async def holiday_end_next(callback: CallbackQuery, state: FSMContext):
    _, _, y, m = callback.data.split("_")
    year, month = int(y), int(m)
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    await state.update_data(holiday_end_year=year, holiday_end_month=month)
    await callback.message.edit_reply_markup(reply_markup=calendar_keyboard(year, month, prefix="holiday_end"))
    await callback.answer()

@router.callback_query(AddHoliday.waiting_end_date, F.data.startswith("holiday_end_day_"))
async def holiday_end_day_selected(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    year, month, day = int(parts[3]), int(parts[4]), int(parts[5])
    end_date = date(year, month, day)

    data = await state.get_data()
    start_date = data["start_date"]
    if end_date < start_date:
        await callback.answer("❌ Кінцева дата не може бути раніше початкової!", show_alert=True)
        return

    await state.update_data(end_date=end_date)
    await callback.message.edit_text(
        "📝 Введіть опис канікул (або натисніть /skip для пропуску):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="/skip", callback_data="holiday_desc_skip")]
        ])
    )
    await state.set_state(AddHoliday.waiting_description)
    await callback.answer()

@router.callback_query(AddHoliday.waiting_end_date, F.data == "holiday_end_cancel")
async def holiday_end_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Додавання скасовано.", reply_markup=holidays_management_keyboard())
    await callback.answer()

# ---- Обробка опису ----
@router.callback_query(AddHoliday.waiting_description, F.data == "holiday_desc_skip")
async def holiday_desc_skip(callback: CallbackQuery, state: FSMContext, db):
    await state.update_data(description=None)
    data = await state.get_data()
    await show_confirmation(callback.message, data, state)
    await callback.answer()

@router.message(AddHoliday.waiting_description)
async def holiday_desc_input(message: Message, state: FSMContext):
    desc = message.text.strip()
    if len(desc) > 500:
        await message.answer("❌ Опис занадто довгий. Максимум 500 символів.")
        return
    await state.update_data(description=desc)
    data = await state.get_data()
    await show_confirmation(message, data, state)

async def show_confirmation(msg: Message, data: dict, state: FSMContext):
    start = data["start_date"].strftime("%d.%m.%Y")
    end = data["end_date"].strftime("%d.%m.%Y")
    desc = data.get("description")
    text = (
        f"📚 <b>Підтвердження канікул:</b>\n\n"
        f"📅 Початок: <b>{start}</b>\n"
        f"📅 Кінець: <b>{end}</b>"
    )
    if desc:
        text += f"\n📝 Опис: {html.escape(desc)}"
    text += "\n\nПідтвердити?"
    await msg.answer(text, reply_markup=confirm_cancel_keyboard(), parse_mode="HTML")
    await state.set_state(AddHoliday.waiting_confirm)

@router.callback_query(AddHoliday.waiting_confirm, F.data == "confirm_yes")
async def confirm_add_holiday(callback: CallbackQuery, state: FSMContext, db):
    data = await state.get_data()
    await add_holiday(db, data["start_date"], data["end_date"], data.get("description"))
    await state.clear()
    await callback.message.edit_text("✅ Канікули додано!", reply_markup=holidays_management_keyboard())
    await callback.answer()

@router.callback_query(AddHoliday.waiting_confirm, F.data == "confirm_no")
async def cancel_add_holiday(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Додавання скасовано.", reply_markup=holidays_management_keyboard())
    await callback.answer()

# ================== ВИДАЛЕННЯ КАНІКУЛ ==================
@router.callback_query(F.data == "holiday_delete")
async def delete_holiday_list(callback: CallbackQuery, db):
    holidays = await get_all_holidays(db)
    if not holidays:
        await callback.message.edit_text("📭 Немає канікул для видалення.", reply_markup=holidays_management_keyboard())
        await callback.answer()
        return

    kb = []
    for h in holidays:
        start = h["start_date"].strftime("%d.%m.%Y")
        end = h["end_date"].strftime("%d.%m.%Y")
        desc = f" — {h['description']}" if h.get("description") else ""
        label = f"{start} – {end}{desc}"
        kb.append([InlineKeyboardButton(text=label, callback_data=f"holiday_del_{h['id']}")])
    kb.append([InlineKeyboardButton(text="↩️ Назад", callback_data="admin_holidays")])

    await callback.message.edit_text(
        "🗑 <b>Оберіть канікули для видалення:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("holiday_del_"))
async def confirm_delete_holiday(callback: CallbackQuery, db):
    holiday_id = int(callback.data.split("_")[2])
    row = await db.fetchrow("SELECT start_date, end_date, description FROM holidays WHERE id=$1", holiday_id)
    if not row:
        await callback.answer("❌ Запис не знайдено.")
        return

    start = row["start_date"].strftime("%d.%m.%Y")
    end = row["end_date"].strftime("%d.%m.%Y")
    desc = f" — {row['description']}" if row.get("description") else ""
    text = f"⚠️ <b>Видалити канікули?</b>\n\n{start} – {end}{desc}"
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Так, видалити", callback_data=f"holiday_del_confirm_{holiday_id}"),
             InlineKeyboardButton(text="❌ Скасувати", callback_data="admin_holidays")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("holiday_del_confirm_"))
async def execute_delete_holiday(callback: CallbackQuery, db):
    holiday_id = int(callback.data.split("_")[3])
    await delete_holiday(db, holiday_id)
    await callback.message.edit_text("✅ Канікули видалено!", reply_markup=holidays_management_keyboard())
    await callback.answer()
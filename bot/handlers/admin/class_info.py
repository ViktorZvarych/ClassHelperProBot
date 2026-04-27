from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline.admin import confirm_cancel_keyboard
from bot.keyboards.inline.common import cancel_button
from bot.states.fsm import EditClassName
from db.queries.class_info import get_class_info, update_class_info

router = Router()

@router.callback_query(F.data == "admin_class_info")
async def edit_class_info_start(callback: CallbackQuery, state: FSMContext, db):
    info = await get_class_info(db)
    await callback.message.edit_text(
        f"🏷 <b>Редагування назви класу</b>\n\n"
        f"Поточна назва: <b>{info['class_number']}-{info['class_letter']}</b>\n\n"
        f"Введіть новий номер класу (1–11):",
        reply_markup=cancel_button(),
        parse_mode="HTML"
    )
    await state.set_state(EditClassName.waiting_number)
    await callback.answer()

@router.message(EditClassName.waiting_number)
async def process_class_number(message: Message, state: FSMContext):
    try:
        number = int(message.text.strip())
        if number < 1 or number > 11:
            await message.answer("❌ Номер класу має бути від 1 до 11. Спробуйте ще раз:")
            return
    except ValueError:
        await message.answer("❌ Введіть ціле число від 1 до 11:")
        return
    
    await state.update_data(class_number=number)
    await message.answer(
        "Введіть нову літеру класу (1–2 символи):",
        reply_markup=cancel_button()
    )
    await state.set_state(EditClassName.waiting_letter)

@router.message(EditClassName.waiting_letter)
async def process_class_letter(message: Message, state: FSMContext, db):
    letter = message.text.strip().upper()
    if len(letter) < 1 or len(letter) > 2:
        await message.answer("❌ Літера класу має містити 1–2 символи. Спробуйте ще раз:")
        return
    
    data = await state.get_data()
    new_number = data["class_number"]
    
    info = await get_class_info(db)
    old_name = f"{info['class_number']}-{info['class_letter']}"
    new_name = f"{new_number}-{letter}"
    
    await state.update_data(class_letter=letter)
    
    await message.answer(
        f"🏷 <b>Підтвердження зміни назви класу:</b>\n\n"
        f"Стара назва: <b>{old_name}</b>\n"
        f"Нова назва: <b>{new_name}</b>\n\n"
        f"Підтвердити?",
        reply_markup=confirm_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(EditClassName.waiting_confirm)

@router.callback_query(EditClassName.waiting_confirm, F.data == "confirm_yes")
async def confirm_edit_class(callback: CallbackQuery, state: FSMContext, db):
    data = await state.get_data()
    await update_class_info(db, data["class_number"], data["class_letter"])
    await state.clear()
    
    from bot.keyboards.inline.admin import admin_panel_keyboard
    await callback.message.edit_text(
        f"✅ Назву класу змінено на <b>{data['class_number']}-{data['class_letter']}</b>!",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(EditClassName.waiting_confirm, F.data == "confirm_no")
async def cancel_edit_class(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from bot.keyboards.inline.admin import admin_panel_keyboard
    await callback.message.edit_text(
        "❌ Зміну назви класу скасовано.",
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()
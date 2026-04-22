# Канікули

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline.admin import holidays_management_keyboard
from bot.states.fsm import AddHoliday
from db.queries.holidays import get_all_holidays, add_holiday, delete_holiday
from services.schedule import parse_date_input

router = Router()

@router.callback_query(F.data == "admin_holidays")
async def manage_holidays(callback: CallbackQuery, db):
    holidays = await get_all_holidays(db)
    text = "Канікули:\n" + "\n".join(f"{h['id']}. {h['start_date']} - {h['end_date']} {h.get('description','')}" for h in holidays)
    await callback.message.edit_text(text, reply_markup=holidays_management_keyboard())
    await callback.answer()
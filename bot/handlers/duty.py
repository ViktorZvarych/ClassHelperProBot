# Чергування (перегляд + підтвердження)

import html
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import settings
from bot.keyboards.inline.duty import duty_menu_keyboard, duty_confirm_keyboard
from bot.states.fsm import ConfirmDuty
from services.schedule import is_school_day, format_date_uk, parse_date_input
from db.queries.duty import get_duty_status_for_date, get_pending_duty_students, confirm_duty_completion, get_duty_history
from db.queries.students import get_student_by_id

router = Router()

@router.message(F.text == "🧹 Чергування")
async def duty_menu(message: Message):
    await message.answer("Оберіть дію:", reply_markup=duty_menu_keyboard())

@router.callback_query(F.data == "duty_today")
async def duty_today(callback: CallbackQuery, db):
    tz = ZoneInfo(settings.TIMEZONE)
    today = datetime.now(tz).date()
    await show_duty_for_date(callback.message, today, db)
    await callback.answer()

@router.callback_query(F.data == "duty_tomorrow")
async def duty_tomorrow(callback: CallbackQuery, db):
    tz = ZoneInfo(settings.TIMEZONE)
    tomorrow = datetime.now(tz).date() + timedelta(days=1)
    await show_duty_for_date(callback.message, tomorrow, db, is_tomorrow=True)
    await callback.answer()

@router.callback_query(F.data == "duty_history")
async def duty_history(callback: CallbackQuery, db):
    tz = ZoneInfo(settings.TIMEZONE)
    end = datetime.now(tz).date()
    start = end - timedelta(days=5)
    history = await get_duty_history(start, end, db)
    if not history:
        await callback.message.edit_text("📭 Історія чергувань за останні 5 днів відсутня.")
    else:
        text = f"🗓 Історія чергувань ({start.strftime('%d.%m')} – {end.strftime('%d.%m')}):\n\n"
        for day_str, entries in history.items():
            text += f"🔹 {day_str}:\n"
            for e in entries:
                status_icon = {"pending": "⏳", "completed": "✅", "replaced": "↩️", "absent": "🚫"}.get(e["status"], "❓")
                name = html.escape(e["full_name"])
                if e["status"] == "replaced" and e.get("replaced_by_name"):
                    text += f"  • {name} {status_icon} (замінений {html.escape(e['replaced_by_name'])})\n"
                elif e["status"] == "replaced":
                    text += f"  • {name} {status_icon}\n"
                elif e.get("replaced_by_name"):
                    text += f"  • {name} {status_icon} (замість {html.escape(e['replaced_by_name'])})\n"
                else:
                    text += f"  • {name} {status_icon}\n"
            text += "\n"
        await callback.message.edit_text(text)
    await callback.answer()

@router.callback_query(F.data == "duty_confirm")
async def duty_confirm_start(callback: CallbackQuery, state: FSMContext, db, student):
    # Запит дати
    from bot.keyboards.inline.common import date_select_keyboard
    await callback.message.edit_text("Оберіть дату чергування:", reply_markup=date_select_keyboard())
    await state.set_state(ConfirmDuty.waiting_date)
    await callback.answer()

async def show_duty_for_date(msg: Message, target_date: date, db, is_tomorrow=False):
    school_day, _ = await is_school_day(target_date, db)
    if not school_day:
        await msg.edit_text(f"📭 {format_date_uk(target_date)} — ненавчальний день.")
        return
    duty_list = await get_duty_status_for_date(target_date, db)
    if not duty_list:
        if is_tomorrow:
            await msg.edit_text("Чергові на завтра ще не визначені. Спробуйте після 20:00.")
        else:
            await msg.edit_text("📭 Чергових на цю дату не призначено.")
        return
    text = f"🧹 Чергові на {format_date_uk(target_date)}:\n\n"
    for d in duty_list:
        status_icon = {"pending": "⏳ (очікує)", "completed": "✅ (виконано)", "replaced": "↩️ (замінений)", "absent": "🚫 (відсутній)"}.get(d["status"], "")
        name = html.escape(d["full_name"])
        if d.get("replaced_by_name"):
            text += f"• {name} {status_icon} (замість {html.escape(d['replaced_by_name'])})\n"
        else:
            text += f"• {name} {status_icon}\n"
    await msg.edit_text(text)

# Продовження FSM для підтвердження чергування...
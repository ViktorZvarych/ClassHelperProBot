from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.queries.students import get_all_active_students

def election_menu_keyboard():
    """Головне меню виборів."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ️ Інформація", callback_data="election_info")],
        [InlineKeyboardButton(text="🚫 Вотум недовіри", callback_data="no_confidence_start")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
    ])

def no_confidence_confirm_keyboard():
    """Підтвердження ініціації вотуму недовіри."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Так, ініціювати", callback_data="no_confidence_confirm_yes")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="no_confidence_confirm_no")]
    ])

def vote_no_confidence_keyboard():
    """Клавіатура для голосування за/проти вотуму."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ За", callback_data="vote_no_confidence_yes")],
        [InlineKeyboardButton(text="❌ Проти", callback_data="vote_no_confidence_no")]
    ])

def candidate_list_keyboard(candidates, election_id):
    """Клавіатура зі списком кандидатів."""
    kb = []
    for c in candidates:
        kb.append([InlineKeyboardButton(
            text=c['full_name'],
            callback_data=f"vote_candidate_{election_id}_{c['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def resign_confirm_keyboard():
    """Підтвердження складання повноважень."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Так, скласти повноваження", callback_data="resign_confirm_yes")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="resign_confirm_no")]
    ])
# Усі FSM StatesGroup

from aiogram.fsm.state import State, StatesGroup

class Broadcast(StatesGroup):
    waiting_text = State()
    waiting_confirm = State()

class AddHomework(StatesGroup):
    waiting_subject = State()
    waiting_date = State()
    waiting_text = State()
    waiting_is_control = State()
    waiting_confirm = State()

class EditHomework(StatesGroup):
    waiting_select_record = State()
    waiting_field = State()
    waiting_new_value = State()
    waiting_confirm = State()

class AddStudent(StatesGroup):
    waiting_name = State()
    waiting_group = State()
    waiting_role = State()
    waiting_telegram_id = State()
    waiting_confirm = State()

class EditClassName(StatesGroup):
    waiting_number = State()
    waiting_letter = State()
    waiting_confirm = State()

class AddHoliday(StatesGroup):
    waiting_start_date = State()
    waiting_end_date = State()
    waiting_description = State()
    waiting_confirm = State()

class ConfirmDuty(StatesGroup):
    waiting_date = State()
    waiting_student = State()
    waiting_confirm = State()

class GetHomeworkByDate(StatesGroup):
    waiting_date = State()
from aiogram import Dispatcher
from . import start, schedule, homework, duty, broadcast, common
from .admin import panel, absence, homework as admin_homework, students, holidays, class_info

def setup_routers(dp: Dispatcher):
    dp.include_router(start.router)
    dp.include_router(schedule.router)
    dp.include_router(homework.router)
    dp.include_router(duty.router)
    dp.include_router(broadcast.router)
    # Admin routers
    dp.include_router(panel.router)
    dp.include_router(absence.router)
    dp.include_router(admin_homework.router)
    dp.include_router(students.router)
    dp.include_router(holidays.router)
    dp.include_router(class_info.router)
    # Common must be last (catch-all)
    dp.include_router(common.router)
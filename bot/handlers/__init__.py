from aiogram import Dispatcher
from . import start, schedule, homework, duty, broadcast, common, election
from .admin import panel, absence, homework as admin_homework, students, holidays, class_info, election as admin_election, instruction

def setup_routers(dp: Dispatcher):
    dp.include_router(start.router)
    dp.include_router(schedule.router)
    dp.include_router(homework.router)
    dp.include_router(duty.router)
    dp.include_router(broadcast.router)    
    dp.include_router(election.router)
    # Admin routers
    dp.include_router(panel.router)
    dp.include_router(absence.router)
    dp.include_router(admin_homework.router)
    dp.include_router(students.router)
    dp.include_router(holidays.router)
    dp.include_router(class_info.router)
    dp.include_router(admin_election.router)
    dp.include_router(instruction.router)
    # Common must be last (catch-all)
    dp.include_router(common.router)
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import achievements, common, daily_challenge, reading, statistics, vocabulary, listening


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(common.router)
    dispatcher.include_router(vocabulary.router)
    dispatcher.include_router(reading.router)
    dispatcher.include_router(listening.router)
    dispatcher.include_router(daily_challenge.router)
    dispatcher.include_router(statistics.router)
    dispatcher.include_router(achievements.router)
    return dispatcher

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import achievements, common, daily_challenge, reading, statistics, vocabulary, listening


import logging
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())

    @dispatcher.error()
    async def global_error_handler(event: ErrorEvent) -> None:
        logger.exception("Global error handler caught unhandled exception: %s", event.exception)
        if event.update.callback_query:
            try:
                await event.update.callback_query.answer(
                    "⚠️ An unexpected error occurred. Please try again.",
                    show_alert=True,
                )
            except Exception:
                pass
        elif event.update.message:
            try:
                await event.update.message.answer("⚠️ An unexpected error occurred. Please try again.")
            except Exception:
                pass

    dispatcher.include_router(common.router)
    dispatcher.include_router(vocabulary.router)
    dispatcher.include_router(reading.router)
    dispatcher.include_router(listening.router)
    dispatcher.include_router(daily_challenge.router)
    dispatcher.include_router(statistics.router)
    dispatcher.include_router(achievements.router)
    return dispatcher

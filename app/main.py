import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import get_settings
from app.logging_config import configure_logging
from bot.dispatcher import create_dispatcher
from infrastructure.database.engine import (
    create_database_engine,
    create_session_factory,
    init_database,
)


logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    configure_logging(debug=settings.debug)

    engine = create_database_engine(settings.database_url, echo=settings.debug)
    session_factory = create_session_factory(engine)

    await init_database(engine)

    bot = Bot(
        token=settings.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = create_dispatcher()

    dispatcher["settings"] = settings
    dispatcher["session_factory"] = session_factory

    logger.info("Starting TOEFL Telegram bot")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

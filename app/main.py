import asyncio
import logging
import os

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from app.config import get_settings
from app.logging_config import configure_logging
from bot.dispatcher import create_dispatcher
from infrastructure.database.engine import (
    create_database_engine,
    create_session_factory,
    init_database,
)


logger = logging.getLogger(__name__)


async def _start_health_server(port: int) -> web.AppRunner:
    """Start a lightweight HTTP health-check server for cloud platforms (e.g. Render)."""
    app = web.Application()

    async def health_handler(request: web.Request) -> web.Response:
        return web.json_response(
            {"status": "ok", "service": "toefl-telegram-bot"},
            status=200,
        )

    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health-check HTTP server listening on 0.0.0.0:{port}")
    return runner


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

    # Start healthcheck server if PORT is provided by the hosting platform (e.g. Render)
    port_env = os.getenv("PORT")
    web_runner: web.AppRunner | None = None
    if port_env:
        try:
            port = int(port_env)
            web_runner = await _start_health_server(port)
        except ValueError:
            logger.warning(f"Invalid PORT environment variable: {port_env}")

    logger.info("Starting TOEFL Telegram bot")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        if web_runner is not None:
            await web_runner.cleanup()
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())


import logging
import os
from contextlib import asynccontextmanager
from hmac import compare_digest
from typing import Any

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logging_config import configure_logging
from bot.dispatcher import create_dispatcher
from infrastructure.database.engine import (
    create_database_engine,
    create_session_factory,
    init_database,
)

logger = logging.getLogger(__name__)

# Application settings and singletons
settings = get_settings()
configure_logging(debug=settings.debug)
webhook_secret_token = settings.webhook_secret_token

is_serverless = bool(os.getenv("VERCEL"))
engine = create_database_engine(settings.database_url, echo=settings.debug, is_serverless=is_serverless)
session_factory = create_session_factory(engine)

bot = Bot(
    token=settings.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dispatcher = create_dispatcher()
dispatcher["settings"] = settings
dispatcher["session_factory"] = session_factory

_db_initialized = False


async def ensure_db_initialized() -> None:
    """Ensure database schema is created on cold start."""
    global _db_initialized
    if not _db_initialized:
        try:
            await init_database(engine)
            _db_initialized = True
        except Exception:
            logger.exception("Failed to initialize database schema")
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_db_initialized()
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        webhook_url = f"{render_url.rstrip('/')}/api/webhook"
        logger.info("Automatically setting webhook on Render: %s", webhook_url)
        try:
            res = await bot.set_webhook(url=webhook_url, secret_token=webhook_secret_token)
            logger.info("Successfully registered webhook with Telegram: %s", res)
        except Exception:
            logger.exception("Failed to set webhook on startup")

    yield

    await bot.session.close()
    await engine.dispose()


app = FastAPI(title="TOEFL Telegram Bot Serverless API", lifespan=lifespan)


@app.get("/")
@app.get("/health")
@app.get("/api")
@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "toefl-telegram-bot"}


@app.post("/webhook")
@app.post("/api/webhook")
async def telegram_webhook(request: Request) -> Response:
    """Process incoming Telegram updates from webhook."""
    if not compare_digest(
        request.headers.get("x-telegram-bot-api-secret-token", ""),
        webhook_secret_token,
    ):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    try:
        update_data = await request.json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dispatcher.feed_update(bot, update)
        return JSONResponse(content={"ok": True}, status_code=status.HTTP_200_OK)
    except Exception:
        logger.exception("Error processing webhook update")
        return JSONResponse(
            content={"ok": False},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.get("/webhook_info")
@app.get("/api/webhook_info")
async def get_webhook_info() -> dict[str, Any]:
    """Inspect current Telegram webhook status."""
    info = await bot.get_webhook_info()
    return {
        "url": info.url,
        "has_custom_certificate": info.has_custom_certificate,
        "pending_update_count": info.pending_update_count,
        "last_error_date": info.last_error_date,
        "last_error_message": info.last_error_message,
    }

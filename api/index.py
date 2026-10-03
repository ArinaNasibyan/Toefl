import logging
from contextlib import asynccontextmanager
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


import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_db_initialized()
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        webhook_url = f"{render_url.rstrip('/')}/api/webhook"
        logger.info("Automatically setting webhook on Render: %s", webhook_url)
        try:
            res = await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
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
    try:
        update_data = await request.json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dispatcher.feed_update(bot, update)
        return JSONResponse(content={"ok": True}, status_code=status.HTTP_200_OK)
    except Exception as exc:
        logger.exception("Error processing webhook update: %s", exc)
        # Always return 200 OK so Telegram does not aggressively retry failed updates
        return JSONResponse(content={"ok": False, "error": str(exc)}, status_code=status.HTTP_200_OK)


@app.get("/set_webhook")
@app.get("/api/set_webhook")
async def set_webhook(request: Request) -> dict[str, Any]:
    """Helper endpoint to register the current Vercel deployment URL with Telegram."""
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if host and "localhost" not in host and "127.0.0.1" not in host:
        base_url = f"https://{host}"
    else:
        base_url = str(request.base_url).rstrip("/")
        if base_url.startswith("http://") and "localhost" not in base_url and "127.0.0.1" not in base_url:
            base_url = "https://" + base_url.split("http://", 1)[1]

    webhook_url = f"{base_url}/api/webhook"
    result = await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    return {
        "ok": True,
        "webhook_url": webhook_url,
        "result": result,
    }


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

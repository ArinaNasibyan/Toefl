import importlib
import json
from unittest.mock import AsyncMock

import pytest
from fastapi import Request

from app.config import get_settings


@pytest.mark.asyncio
async def test_webhook_retries_failed_updates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123456:TEST_TOKEN")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    get_settings.cache_clear()
    api = importlib.import_module("api.index")
    monkeypatch.setattr(
        api.dispatcher,
        "feed_update",
        AsyncMock(side_effect=RuntimeError("database unavailable")),
    )

    body = json.dumps({"update_id": 1}).encode()

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": body, "more_body": False}

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/webhook",
            "headers": [(b"x-telegram-bot-api-secret-token", api.webhook_secret_token.encode())],
        },
        receive,
    )

    try:
        response = await api.telegram_webhook(request)
        assert response.status_code == 500
        assert b"database unavailable" not in response.body
    finally:
        await api.bot.session.close()
        await api.engine.dispose()
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_webhook_rejects_missing_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123456:TEST_TOKEN")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    get_settings.cache_clear()
    api = importlib.import_module("api.index")
    feed_update = AsyncMock()
    monkeypatch.setattr(api.dispatcher, "feed_update", feed_update)

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(
        {"type": "http", "method": "POST", "path": "/api/webhook", "headers": []},
        receive,
    )

    try:
        response = await api.telegram_webhook(request)
        assert response.status_code == 403
        feed_update.assert_not_awaited()
    finally:
        await api.bot.session.close()
        await api.engine.dispose()
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_only_primary_render_service_registers_webhook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123456:TEST_TOKEN")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    get_settings.cache_clear()
    api = importlib.import_module("api.index")
    monkeypatch.setattr(api, "ensure_db_initialized", AsyncMock())
    set_webhook = AsyncMock()
    monkeypatch.setattr(api.bot, "set_webhook", set_webhook)

    try:
        monkeypatch.setenv(
            "RENDER_EXTERNAL_URL", "https://toefl-telegram-bot-fksd.onrender.com"
        )
        async with api.lifespan(api.app):
            pass
        set_webhook.assert_not_awaited()

        monkeypatch.setenv(
            "RENDER_EXTERNAL_URL", "https://toefl-telegram-bot-h5u5.onrender.com"
        )
        async with api.lifespan(api.app):
            pass
        set_webhook.assert_awaited_once_with(
            url="https://toefl-telegram-bot-h5u5.onrender.com/api/webhook",
            secret_token=api.webhook_secret_token,
        )
    finally:
        get_settings.cache_clear()

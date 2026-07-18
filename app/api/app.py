from contextlib import asynccontextmanager
from typing import Any

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException

from app.bot.factory import create_bot, create_dispatcher
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.bot = create_bot(settings)
    app.state.dispatcher = create_dispatcher()
    if settings.auto_set_webhook and settings.public_webhook_base_url:
        await app.state.bot.set_webhook(
            f"{settings.public_webhook_base_url}/telegram/webhook",
            secret_token=settings.telegram_webhook_secret,
            drop_pending_updates=False,
        )
    yield
    await app.state.bot.session.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Вечерние измерения", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    @app.post("/telegram/webhook")
    async def telegram_webhook(
        payload: dict[str, Any],
        x_telegram_bot_api_secret_token: str | None = Header(default=None),
    ) -> dict[str, bool]:
        settings: Settings = get_settings()
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
        update = Update.model_validate(payload, context={"bot": app.state.bot})
        await app.state.dispatcher.feed_update(app.state.bot, update)
        return {"ok": True}

    return app


app = create_app()

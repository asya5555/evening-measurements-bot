import asyncio

from aiogram import Bot

from app.core.config import get_settings


async def main() -> None:
    settings = get_settings()
    if settings.public_webhook_base_url is None:
        raise SystemExit("Set PUBLIC_WEBHOOK_BASE_URL first.")
    bot = Bot(settings.telegram_bot_token)
    await bot.set_webhook(
        f"{settings.public_webhook_base_url}/telegram/webhook",
        secret_token=settings.telegram_webhook_secret,
        drop_pending_updates=False,
    )
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

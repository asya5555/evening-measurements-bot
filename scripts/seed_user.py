import asyncio

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.repositories.users import UserRepository


async def main() -> None:
    settings = get_settings()
    if not settings.telegram_allowed_user_ids:
        raise SystemExit("Set TELEGRAM_ALLOWED_USER_IDS first.")
    async with SessionLocal() as session:
        repo = UserRepository(session)
        for telegram_id in settings.telegram_allowed_user_ids:
            await repo.get_or_create(telegram_id, username=None, first_name=None)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())

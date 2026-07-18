from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserSettings
from app.schemas.settings import UserSettings as UserSettingsSchema


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, telegram_user_id: int, username: str | None, first_name: str | None) -> User:
        user = await self.get_by_telegram_id(telegram_user_id)
        if user:
            return user
        user = User(telegram_user_id=telegram_user_id, username=username, first_name=first_name)
        self.session.add(user)
        await self.session.flush()
        defaults = UserSettingsSchema()
        self.session.add(
            UserSettings(
                user_id=user.id,
                timezone=defaults.timezone,
                first_reminder_time=defaults.first_reminder_time,
                second_reminder_time=defaults.second_reminder_time,
                reminders_enabled=defaults.reminders_enabled,
                required_sections=defaults.required_sections,
                daily_analytics_enabled=defaults.daily_analytics_enabled,
                weekly_report_enabled=defaults.weekly_report_enabled,
                monthly_report_enabled=defaults.monthly_report_enabled,
                mood_scale=defaults.mood_scale,
                tracked_measurements=defaults.tracked_measurements,
            )
        )
        await self.session.flush()
        return user

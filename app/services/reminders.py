from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from app.services.date_utils import reminder_datetime


@dataclass(frozen=True)
class ReminderPlan:
    observed_on: date
    notification_on: date
    first_for_utc: datetime
    second_for_utc: datetime
    first_idempotency_key: str
    second_idempotency_key: str


def build_daily_reminder_plan(
    user_id: int,
    observed_on: date,
    first_reminder_time: str,
    second_reminder_time: str,
    timezone_name: str,
) -> ReminderPlan:
    notification_on = observed_on + timedelta(days=1)
    first_local = reminder_datetime(notification_on, first_reminder_time, timezone_name)
    second_local = reminder_datetime(notification_on, second_reminder_time, timezone_name)
    return ReminderPlan(
        observed_on=observed_on,
        notification_on=notification_on,
        first_for_utc=first_local.astimezone(UTC),
        second_for_utc=second_local.astimezone(UTC),
        first_idempotency_key=f"{user_id}:{observed_on.isoformat()}:first-reminder",
        second_idempotency_key=f"{user_id}:{observed_on.isoformat()}:second-reminder",
    )


def first_reminder_text() -> str:
    return (
        "Привет! ☀️\n"
        "Давай зафиксируем вчерашний день.\n\n"
        "Можешь рассказать всё одним сообщением, несколькими сообщениями, голосовым или фотографиями. "
        "Я сама разложу всё по разделам."
    )


def second_reminder_text() -> str:
    return "Напоминаю про вчерашнюю запись 🙂\nЕсли сейчас неудобно — ничего страшного, можно заполнить позже."


def missed_days_text(missing_dates: list[date]) -> str:
    formatted = "\n".join(f"• {day.strftime('%d.%m.%Y')}" for day in missing_dates)
    return f"У нас нет записей за:\n\n{formatted}\n\nНачнём с {missing_dates[0].strftime('%d.%m.%Y')}?"

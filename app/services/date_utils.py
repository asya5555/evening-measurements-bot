from datetime import date, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

WEEKDAY_FORMS = {
    0: ("понедельник", "понедельника", "понедельнику", "понедельнике"),
    1: ("вторник", "вторника", "вторнику", "вторнике"),
    2: ("среда", "среду", "среды", "среде"),
    3: ("четверг", "четверга", "четвергу", "четверге"),
    4: ("пятница", "пятницу", "пятницы", "пятнице"),
    5: ("суббота", "субботу", "субботы", "субботе"),
    6: ("воскресенье", "воскресенья", "воскресенью"),
}


def get_timezone(timezone_name: str) -> tzinfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        if timezone_name == "Europe/Tbilisi":
            return timezone(timedelta(hours=4), name="Europe/Tbilisi")
        raise


def user_now(timezone_name: str) -> datetime:
    return datetime.now(get_timezone(timezone_name))


def default_observed_date(timezone_name: str, now: datetime | None = None) -> date:
    current = now or user_now(timezone_name)
    return current.date() - timedelta(days=1)


def observed_date_from_command(command: str, timezone_name: str, now: datetime | None = None) -> date:
    current = now or user_now(timezone_name)
    today = current.date()
    if command == "/today":
        return today
    if command == "/yesterday":
        return today - timedelta(days=1)
    return default_observed_date(timezone_name, current)


def previous_weekday(target_weekday: int, today: date) -> date:
    days_back = (today.weekday() - target_weekday) % 7
    return today if days_back == 0 else today - timedelta(days=days_back)


def _explicit_dates_from_text(text: str, today: date) -> set[date]:
    lowered = text.lower().replace("ё", "е")
    lowered_without_pozavchera = lowered.replace("позавчера", "")
    explicit_dates: set[date] = set()

    if "позавчера" in lowered:
        explicit_dates.add(today - timedelta(days=2))
    if any(marker in lowered_without_pozavchera for marker in ("вчера", "вчераш", "ко вчера")):
        explicit_dates.add(today - timedelta(days=1))
    if any(marker in lowered for marker in ("сегодня", "уже сегодня")):
        explicit_dates.add(today)

    for weekday, forms in WEEKDAY_FORMS.items():
        if any(form in lowered for form in forms):
            explicit_dates.add(previous_weekday(weekday, today))

    return explicit_dates


def infer_observed_date(
    text: str,
    timezone_name: str,
    now: datetime | None = None,
    default_on: date | None = None,
) -> date | None:
    current = now or user_now(timezone_name)
    explicit_dates = _explicit_dates_from_text(text, current.date())
    if len(explicit_dates) > 1:
        return None
    if explicit_dates:
        return explicit_dates.pop()
    if default_on is not None:
        return default_on
    return default_observed_date(timezone_name, current)


def date_needs_clarification(text: str, timezone_name: str, now: datetime | None = None) -> bool:
    current = now or user_now(timezone_name)
    return len(_explicit_dates_from_text(text, current.date())) > 1


def reminder_datetime(notification_on: date, time_hhmm: str, timezone_name: str) -> datetime:
    hour, minute = [int(part) for part in time_hhmm.split(":", maxsplit=1)]
    return datetime(
        notification_on.year,
        notification_on.month,
        notification_on.day,
        hour,
        minute,
        tzinfo=get_timezone(timezone_name),
    )

from datetime import date, timedelta


def missing_observed_dates(start_on: date, end_on: date, existing_dates: set[date]) -> list[date]:
    if end_on < start_on:
        return []
    missing: list[date] = []
    current = start_on
    while current <= end_on:
        if current not in existing_dates:
            missing.append(current)
        current += timedelta(days=1)
    return missing


def next_missing_date(missing_dates: list[date]) -> date | None:
    return missing_dates[0] if missing_dates else None


def missed_days_prompt(missing_dates: list[date]) -> str:
    formatted = "\n".join(f"• {day.strftime('%d.%m.%Y')}" for day in missing_dates)
    return f"У нас нет записей за:\n\n{formatted}\n\nНачнём с {missing_dates[0].strftime('%d.%m.%Y')}?"


def backlog_prompt() -> str:
    return "У нас накопилось несколько незаполненных дней.\n\nЧто сделаем?"

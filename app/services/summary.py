from datetime import date

from app.schemas.entry import DailyEntryData


def compact_entry_summary(observed_on: date, data: DailyEntryData) -> str:
    lines = [f"Вот что я записала за {observed_on.strftime('%d.%m.%Y')}:"]
    lines.append(f"Сон: {format_sleep(data)}")
    lines.append(f"Отёки: {format_optional_score(data.edema.score)}")
    lines.append(f"Вода и напитки: {format_drinks(data)}")
    lines.append(f"Питание: {data.nutrition.free_description or 'не указано'}")
    lines.append(f"Активность: {format_activity(data)}")
    lines.append(f"Стул: {data.digestion.stool or 'не указано'}")
    lines.append(f"Цикл: {data.cycle.day_number or 'не указано'}")
    lines.append(f"Настроение: {data.mood.description or data.mood.score or 'не указано'}")
    lines.append(f"Концентрация: {data.focus.description or data.focus.score or 'не указано'}")
    extra = ", ".join(data.extra.keys()) if data.extra else "нет"
    lines.append(f"Дополнительно: {extra}")
    return "\n".join(lines)


def format_sleep(data: DailyEntryData) -> str:
    sleep = data.sleep
    if not any([sleep.fell_asleep_at, sleep.final_wake_at, sleep.total_duration_minutes]):
        return "не указано"
    base = f"{sleep.fell_asleep_at or '?'} - {sleep.final_wake_at or '?'}"
    if sleep.additional_periods:
        base += f"; дополнительные периоды: {len(sleep.additional_periods)}"
    return base


def format_optional_score(score: int | None) -> str:
    return "не указано" if score is None else f"{score}/10"


def format_drinks(data: DailyEntryData) -> str:
    parts: list[str] = []
    if data.drinks.pure_water_ml:
        parts.append(f"вода {data.drinks.pure_water_ml} мл")
    if data.drinks.tea_ml:
        parts.append(f"чай около {data.drinks.tea_ml} мл")
    if data.drinks.coffee_ml:
        parts.append(f"кофе около {data.drinks.coffee_ml} мл")
    parts.extend(data.drinks.other_drinks)
    return ", ".join(parts) if parts else "не указано"


def format_activity(data: DailyEntryData) -> str:
    parts = []
    if data.activity.walk:
        parts.append("прогулка")
    if data.activity.exercise:
        parts.append("зарядка")
    if data.activity.workout:
        parts.append(data.activity.workout)
    if data.activity.steps:
        parts.append(f"{data.activity.steps} шагов")
    return ", ".join(parts) if parts else "не указано"

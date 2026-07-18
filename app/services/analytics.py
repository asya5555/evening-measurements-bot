from statistics import median

from app.schemas.entry import DailyEntryData
from app.schemas.reports import DailyAnalysis, Observation, PeriodReport


def daily_analysis(current: DailyEntryData, previous: list[DailyEntryData], observed_on) -> DailyAnalysis:
    edema_values = [item.edema.score for item in previous if item.edema.score is not None]
    comparison = "Пока мало предыдущих записей для сравнения."
    if current.edema.score is not None and len(edema_values) >= 3:
        avg = sum(edema_values) / len(edema_values)
        if current.edema.score < avg:
            comparison = "Сегодня отёки ниже среднего по последним записям."
        elif current.edema.score > avg:
            comparison = "Сегодня отёки выше среднего по последним записям."
        else:
            comparison = "Отёки примерно на уровне последних записей."
    return DailyAnalysis(
        observed_on=observed_on,
        summary="День сохранён в дневнике в согласованном формате.",
        comparison=comparison,
        possible_links="Возможные совпадения стоит оценивать только на серии записей, не по одному дню.",
        reliability=("Надёжность вывода низкая, если заполнены не все разделы или накоплено меньше пяти дней."),
    )


def period_report(period: str, starts_on, ends_on, entries: list[DailyEntryData]) -> PeriodReport:
    filled_days = len(entries)
    observations: list[Observation] = []
    sleep_values = [entry.sleep.total_duration_minutes for entry in entries if entry.sleep.total_duration_minutes]
    edema_values = [entry.edema.score for entry in entries if entry.edema.score is not None]
    active_days = sum(1 for entry in entries if entry.activity.walk or entry.activity.exercise or entry.activity.workout)

    if sleep_values:
        avg_sleep = round(sum(sleep_values) / len(sleep_values))
        observations.append(
            Observation(
                text=f"Средняя продолжительность сна: около {avg_sleep} минут; медиана {round(median(sleep_values))} минут.",
                confidence="medium" if len(sleep_values) >= 4 else "low",
            )
        )
    else:
        observations.append(Observation(text="Пока данных о продолжительности сна недостаточно.", confidence="low"))

    if edema_values:
        observations.append(
            Observation(
                text=f"Диапазон отёков: {min(edema_values)}-{max(edema_values)} из 10.",
                confidence="medium" if len(edema_values) >= 4 else "low",
            )
        )

    observations.append(
        Observation(
            text=f"Активность отмечена в {active_days} из {filled_days} заполненных дней.",
            confidence="medium" if filled_days >= 5 else "low",
        )
    )

    prefix = "Недельный" if period == "week" else "Месячный"
    text_lines = [f"{prefix} отчёт: заполнено дней {filled_days}."]
    text_lines.extend(f"- {item.text} Надёжность: {item.confidence}." for item in observations)
    text_lines.append("Корреляции в отчёте описываются как совпадения, а не доказанные причины.")
    return PeriodReport(
        period=period,  # type: ignore[arg-type]
        starts_on=starts_on,
        ends_on=ends_on,
        filled_days=filled_days,
        missing_data=[] if filled_days else ["Нет заполненных записей за период."],
        observations=observations,
        text="\n".join(text_lines),
    )

import re
from datetime import UTC, date, datetime

from app.schemas.entry import (
    ActivityData,
    DailyEntryData,
    EdemaData,
    ExtractionResult,
    MealItem,
    SleepPeriod,
)
from app.services.date_utils import infer_observed_date
from app.services.required_fields import clarification_questions, missing_required_sections


def heuristic_extract(
    text: str,
    *,
    timezone: str,
    required_sections: list[str],
    today: date | None = None,
    default_observed_on: date | None = None,
) -> ExtractionResult:
    """Deterministic fallback used in tests and when OpenAI is temporarily unavailable."""
    lowered = text.lower()
    data = DailyEntryData()

    sleep_match = re.search(r"с\s+([0-2]?\d)(?::([0-5]\d))?\s+до\s+([0-2]?\d)(?::([0-5]\d))?", lowered)
    if sleep_match:
        start_h, start_m, end_h, end_m = sleep_match.groups()
        data.sleep.fell_asleep_at = f"{int(start_h):02d}:{int(start_m or 0):02d}"
        data.sleep.final_wake_at = f"{int(end_h):02d}:{int(end_m or 0):02d}"

    extra_sleep_matches = re.findall(r"ещ[её]\s+до\s+([0-2]?\d)(?::([0-5]\d))?", lowered)
    for end_h, end_m in extra_sleep_matches:
        data.sleep.additional_periods.append(SleepPeriod(end_time=f"{int(end_h):02d}:{int(end_m or 0):02d}", comment="дополнительный сон"))

    edema_match = re.search(r"от[её]к[иаов]*\D{0,12}([0-9]|10)\s*(?:из|/)\s*10", lowered)
    if not edema_match:
        edema_match = re.search(r"от[её]к[иаов]*\D{0,12}([0-9]|10)", lowered)
    if edema_match:
        data.edema = EdemaData(score=int(edema_match.group(1)))

    water_match = re.search(r"(\d+(?:[,.]\d+)?)\s*(?:л|литр)", lowered)
    if water_match:
        data.drinks.pure_water_ml = int(float(water_match.group(1).replace(",", ".")) * 1000)
    elif "литр воды" in lowered or "л воды" in lowered:
        data.drinks.pure_water_ml = 1000
    if "чай" in lowered:
        data.drinks.tea_ml = data.drinks.tea_ml or 250
    if "кофе" in lowered:
        data.drinks.coffee_ml = data.drinks.coffee_ml or 150

    food_markers = ["ела", "ел ", "питание", "перекус", "завтрак", "обед", "ужин"]
    if any(marker in lowered for marker in food_markers):
        fragment = text
        for marker in ["Ела", "ела", "Ел", "ел"]:
            if marker in text:
                fragment = text.split(marker, maxsplit=1)[1]
                break
        products = [item.strip(" .") for item in re.split(r",|\s+и\s+", fragment) if item.strip(" .") and len(item.strip(" .")) <= 40][:12]
        data.nutrition.free_description = fragment.strip(" .")
        data.nutrition.meals.append(MealItem(products=products))

    data.activity = ActivityData(
        walk="прогул" in lowered,
        exercise="зарядк" in lowered,
        workout="трениров" if "трениров" in lowered else None,
        swimming="плав" if "плав" in lowered else None,
    )

    if "стул" in lowered:
        data.digestion.stool = "упомянут"
        if "норм" in lowered:
            data.digestion.stool = "нормальный"

    cycle_match = re.search(r"(?:день цикла|цикл[а]?)\D{0,12}(\d{1,2})", lowered)
    if cycle_match:
        data.cycle.day_number = int(cycle_match.group(1))
        data.cycle.estimated_phase = estimate_cycle_phase(data.cycle.day_number)
        data.cycle.phase_is_calculated = True

    mood_match = re.search(r"настроени[ея]\s+([^,.]+)", lowered)
    if mood_match:
        data.mood.description = mood_match.group(1).strip()
    if "спокой" in lowered:
        data.mood.calmness = "спокойное"
        data.mood.description = data.mood.description or "спокойное"

    focus_match = re.search(r"концентрац[а-я]+\s+([^,.]+)", lowered)
    if focus_match:
        data.focus.description = focus_match.group(1).strip()
    if "очень высокая" in lowered:
        data.focus.score = 9

    now = datetime.combine(today, datetime.min.time(), tzinfo=UTC) if today else None
    observed_on = infer_observed_date(text, timezone, now, default_on=default_observed_on)
    missing = missing_required_sections(data, required_sections)
    return ExtractionResult(
        observed_on=observed_on,
        data=data,
        missing_required_fields=missing,
        clarification_questions=clarification_questions(missing),
        confidence="medium",
        notes=["fallback_heuristic"],
    )


def estimate_cycle_phase(day_number: int | None) -> str | None:
    if day_number is None:
        return None
    if day_number <= 5:
        return "менструальная"
    if day_number <= 13:
        return "фолликулярная"
    if day_number <= 16:
        return "овуляторная"
    return "лютеиновая"

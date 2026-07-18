from app.schemas.entry import DailyEntryData

SECTION_QUESTIONS = {
    "sleep": "Как сегодня со сном: во сколько примерно уснула и проснулась?",
    "edema": "Как ты оцениваешь отёки по шкале 0-10?",
    "drinks": "Сколько примерно было чистой воды и отдельно чая, кофе или других напитков?",
    "nutrition": "Что сегодня было из еды или перекусов?",
    "activity": "Была ли прогулка, зарядка, тренировка или другая активность?",
    "digestion": "Как было со стулом и пищеварением, если хочешь это отметить?",
    "cycle": "Какой сегодня день цикла, если отслеживаешь?",
    "mood": "Как бы ты описала настроение или оценила его по своей шкале?",
    "focus": "Как сегодня были концентрация и работоспособность?",
    "wellbeing": "Были ли дополнительные симптомы или наблюдения по самочувствию?",
}


def missing_required_sections(data: DailyEntryData, required_sections: list[str]) -> list[str]:
    missing: list[str] = []
    if "sleep" in required_sections and not any([data.sleep.fell_asleep_at, data.sleep.final_wake_at, data.sleep.total_duration_minutes]):
        missing.append("sleep")
    if "edema" in required_sections and data.edema.score is None:
        missing.append("edema")
    if "drinks" in required_sections and not any(
        [data.drinks.pure_water_ml, data.drinks.tea_ml, data.drinks.coffee_ml, data.drinks.other_drinks]
    ):
        missing.append("drinks")
    if "nutrition" in required_sections and not any([data.nutrition.free_description, data.nutrition.meals]):
        missing.append("nutrition")
    if "activity" in required_sections and not any(
        [data.activity.walk, data.activity.exercise, data.activity.workout, data.activity.steps]
    ):
        missing.append("activity")
    if "digestion" in required_sections and not any([data.digestion.stool, data.digestion.discomfort, data.digestion.bloating]):
        missing.append("digestion")
    if "cycle" in required_sections and data.cycle.day_number is None:
        missing.append("cycle")
    if "mood" in required_sections and not any([data.mood.description, data.mood.score]):
        missing.append("mood")
    if "focus" in required_sections and not any([data.focus.description, data.focus.score]):
        missing.append("focus")
    if "wellbeing" in required_sections and not any([data.wellbeing.physical, data.wellbeing.unusual_symptoms, data.wellbeing.comment]):
        missing.append("wellbeing")
    return missing


def clarification_questions(missing_sections: list[str]) -> list[str]:
    return [SECTION_QUESTIONS[section] for section in missing_sections if section in SECTION_QUESTIONS]

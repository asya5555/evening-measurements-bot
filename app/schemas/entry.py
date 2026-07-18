from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field

EntryStatus = Literal["draft", "awaiting_confirmation", "saved", "changed", "cancelled"]


class SleepPeriod(BaseModel):
    start_time: str | None = None
    end_time: str | None = None
    duration_minutes: int | None = None
    comment: str | None = None


class SleepData(BaseModel):
    fell_asleep_at: str | None = None
    final_wake_at: str | None = None
    additional_periods: list[SleepPeriod] = Field(default_factory=list)
    night_wakings: str | None = None
    total_duration_minutes: int | None = None
    quality: str | None = None
    comment: str | None = None


class Measurement(BaseModel):
    name: str
    value: float | None = None
    unit: str | None = None
    comment: str | None = None


class EdemaData(BaseModel):
    score: int | None = Field(default=None, ge=0, le=10)
    localization: str | None = None
    appeared_at: str | None = None
    comment: str | None = None


class DrinksData(BaseModel):
    pure_water_ml: int | None = None
    tea_ml: int | None = None
    coffee_ml: int | None = None
    other_drinks: list[str] = Field(default_factory=list)
    total_estimated_ml: int | None = None
    comment: str | None = None


class MealItem(BaseModel):
    meal_type: str | None = None
    products: list[str] = Field(default_factory=list)
    dish: str | None = None
    amount: str | None = None
    salt: str | None = None
    sauces: list[str] = Field(default_factory=list)
    sweets: list[str] = Field(default_factory=list)
    snacks: list[str] = Field(default_factory=list)
    comment: str | None = None


class NutritionData(BaseModel):
    free_description: str | None = None
    meals: list[MealItem] = Field(default_factory=list)
    approximate_calorie_note: str | None = None
    photos: list[str] = Field(default_factory=list)
    labels_observed: list[str] = Field(default_factory=list)
    comment: str | None = None


class ActivityData(BaseModel):
    walk: bool | None = None
    steps: int | None = None
    exercise: bool | None = None
    workout: str | None = None
    swimming: str | None = None
    duration_minutes: int | None = None
    intensity: str | None = None
    other: list[str] = Field(default_factory=list)
    comment: str | None = None


class DigestionData(BaseModel):
    stool: str | None = None
    discomfort: str | None = None
    bloating: str | None = None
    pain: str | None = None
    other: str | None = None


class CycleData(BaseModel):
    day_number: int | None = None
    last_period_started_on: date | None = None
    estimated_phase: str | None = None
    phase_is_calculated: bool = False
    symptoms: list[str] = Field(default_factory=list)
    comment: str | None = None


class MoodData(BaseModel):
    description: str | None = None
    score: float | None = None
    scale: str | None = None
    emotional_background: str | None = None
    calmness: str | None = None
    anxiety: str | None = None
    irritability: str | None = None
    energy: str | None = None
    comment: str | None = None


class FocusData(BaseModel):
    score: float | None = None
    description: str | None = None
    energy_level: str | None = None
    productivity: str | None = None
    comment: str | None = None


class WellbeingData(BaseModel):
    physical: str | None = None
    pain: str | None = None
    headache: str | None = None
    weakness: str | None = None
    unusual_symptoms: list[str] = Field(default_factory=list)
    medications_or_supplements: list[str] = Field(default_factory=list)
    comment: str | None = None


class DailyEntryData(BaseModel):
    sleep: SleepData = Field(default_factory=SleepData)
    measurements: list[Measurement] = Field(default_factory=list)
    edema: EdemaData = Field(default_factory=EdemaData)
    drinks: DrinksData = Field(default_factory=DrinksData)
    nutrition: NutritionData = Field(default_factory=NutritionData)
    activity: ActivityData = Field(default_factory=ActivityData)
    digestion: DigestionData = Field(default_factory=DigestionData)
    cycle: CycleData = Field(default_factory=CycleData)
    mood: MoodData = Field(default_factory=MoodData)
    focus: FocusData = Field(default_factory=FocusData)
    wellbeing: WellbeingData = Field(default_factory=WellbeingData)
    extra: dict[str, Any] = Field(default_factory=dict)


class DailyEntry(BaseModel):
    entry_date: date
    observed_on: date
    started_at: datetime
    finished_at: datetime | None = None
    status: EntryStatus = "draft"
    raw_messages: list[str] = Field(default_factory=list)
    data: DailyEntryData = Field(default_factory=DailyEntryData)

    @computed_field
    @property
    def has_multiple_sleep_periods(self) -> bool:
        return len(self.data.sleep.additional_periods) > 0


class ExtractionResult(BaseModel):
    observed_on: date | None = None
    data: DailyEntryData = Field(default_factory=DailyEntryData)
    missing_required_fields: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    notes: list[str] = Field(default_factory=list)

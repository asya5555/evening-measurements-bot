from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["low", "medium", "high"]


class Observation(BaseModel):
    text: str
    confidence: Confidence


class DailyAnalysis(BaseModel):
    observed_on: date
    summary: str
    comparison: str
    possible_links: str
    reliability: str


class PeriodReport(BaseModel):
    period: Literal["week", "month"]
    starts_on: date
    ends_on: date
    filled_days: int
    missing_data: list[str] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    text: str

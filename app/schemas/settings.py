from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    timezone: str = "Europe/Tbilisi"
    first_reminder_time: str = "13:00"
    second_reminder_time: str = "18:00"
    reminders_enabled: bool = True
    required_sections: list[str] = Field(default_factory=lambda: ["sleep", "edema", "drinks", "nutrition", "activity", "mood"])
    daily_analytics_enabled: bool = True
    weekly_report_enabled: bool = True
    monthly_report_enabled: bool = True
    mood_scale: str = "0-10"
    tracked_measurements: list[str] = Field(default_factory=lambda: ["weight"])

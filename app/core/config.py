from functools import lru_cache

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_name: str = "evening-measurements"
    database_url: str = "postgresql+asyncpg://diary:diary@localhost:5432/diary"

    telegram_bot_token: str = "replace_me"
    telegram_allowed_user_ids: list[int] = Field(default_factory=list)
    telegram_allowed_usernames: list[str] = Field(default_factory=list)
    telegram_webhook_secret: str = "change-me"
    public_webhook_base_url: AnyUrl | None = None
    auto_set_webhook: bool = False

    openai_api_key: str = "replace_me"
    openai_text_model: str = "gpt-4o-mini"
    openai_vision_model: str = "gpt-4o-mini"
    openai_transcription_model: str = "gpt-4o-mini-transcribe"

    default_timezone: str = "Europe/Tbilisi"
    media_dir: str = "media"
    export_dir: str = "exports"
    media_retention_days: int = 14
    export_retention_hours: int = 24
    max_media_bytes: int = 20 * 1024 * 1024
    request_rate_limit_per_minute: int = 30
    log_level: str = "INFO"

    @field_validator("telegram_allowed_user_ids", mode="before")
    @classmethod
    def split_user_ids(cls, value: str | list[int]) -> list[int]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        return [int(item.strip()) for item in value.split(",") if item.strip()]

    @field_validator("telegram_allowed_usernames", mode="before")
    @classmethod
    def split_usernames(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return [item.lower().lstrip("@") for item in value]
        if not value:
            return []
        return [item.strip().lower().lstrip("@") for item in value.split(",") if item.strip()]

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://") and "+asyncpg" not in value:
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

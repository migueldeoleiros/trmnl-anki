from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRMNL_ANKI_", env_file=".env", extra="ignore")

    ankiconnect_url: str = "http://anki:8765"
    ankiconnect_api_key: str | None = None
    ankiconnect_timeout_seconds: float = 10.0
    ankiconnect_sync_timeout_seconds: float = 120.0
    cache_path: Path = Path("/tmp/trmnl-anki-cache.json")
    card_query: str = 'deck:"Core 2000" (is:learn or is:review)'
    fallback_query: str = 'deck:"Core 2000" (is:learn or is:review)'
    min_cards: int = 1
    max_cards: int = 250
    max_query_length: int = Field(default=500, ge=1)
    max_cached_queries: int = Field(default=25, ge=2)
    cadence_minutes: int = Field(default=30, ge=1)
    sync_interval_seconds: int = Field(default=3600, ge=60)
    sync_retry_interval_seconds: int = Field(default=60, ge=5)
    refresh_on_startup: bool = False
    background_sync_enabled: bool = True

    @field_validator("cadence_minutes")
    @classmethod
    def validate_cadence_minutes(cls, value: int) -> int:
        if value not in (15, 30, 60):
            raise ValueError("cadence_minutes must be one of 15, 30, or 60")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

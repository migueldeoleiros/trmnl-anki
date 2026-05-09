from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRMNL_ANKI_", env_file=".env", extra="ignore")

    ankiconnect_url: str = "http://anki:8765"
    ankiconnect_api_key: str | None = None
    ankiconnect_timeout_seconds: float = 10.0
    ankiconnect_sync_timeout_seconds: float = 120.0
    cache_path: Path = Path("/tmp/trmnl-anki-cache.json")
    deck_name: str = "Core 2000"
    card_query: str = 'rated:7 deck:"Core 2000"'
    fallback_query: str = 'deck:"Core 2000"'
    min_cards: int = 1
    max_cards: int = 250
    cadence_minutes: int = Field(default=30, ge=1)
    sync_interval_seconds: int = Field(default=3600, ge=60)
    sync_retry_interval_seconds: int = Field(default=60, ge=5)
    refresh_on_startup: bool = False
    background_sync_enabled: bool = False
    expose_api_docs: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

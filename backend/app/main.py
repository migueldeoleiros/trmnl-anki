from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from .ankiconnect import AnkiConnectClient
from .cache import JsonCardCache
from .config import Settings, get_settings
from .service import CardService


logger = logging.getLogger(__name__)


def build_service(settings: Settings) -> CardService:
    client = AnkiConnectClient(
        settings.ankiconnect_url,
        settings.ankiconnect_timeout_seconds,
        settings.ankiconnect_api_key,
    )
    return CardService(settings, client, JsonCardCache(settings.cache_path))


async def sync_loop(service: CardService, interval_seconds: int) -> None:
    settings = service.settings
    while True:
        result = await service.refresh_from_anki(trigger_sync=True)
        sleep_seconds = interval_seconds if result.get("last_sync_status") == "ok" else settings.sync_retry_interval_seconds
        await asyncio.sleep(sleep_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    service = build_service(settings)
    app.state.settings = settings
    app.state.service = service
    task: asyncio.Task | None = None
    if settings.refresh_on_startup:
        try:
            await service.refresh_from_anki(trigger_sync=False)
        except Exception:
            logger.exception("startup refresh failed; serving existing cache")
    if settings.background_sync_enabled:
        task = asyncio.create_task(sync_loop(service, settings.sync_interval_seconds))
    try:
        yield
    finally:
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        await service.client.aclose()


_settings = get_settings()
app = FastAPI(
    title="TRMNL Anki",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if _settings.expose_api_docs else None,
    redoc_url="/redoc" if _settings.expose_api_docs else None,
    openapi_url="/openapi.json" if _settings.expose_api_docs else None,
)


@app.get("/health")
def health() -> dict:
    service = getattr(app.state, "service", None)
    if service is None:
        return {"status": "starting", "cache_cards": 0, "last_sync_status": None}
    cache = app.state.service.cache.load()
    return {
        "status": "ok",
        "cache_cards": len(cache.get("cards") or []),
        "last_sync_status": cache.get("last_sync_status"),
    }


@app.get("/api/current")
def current() -> dict:
    return app.state.service.current()

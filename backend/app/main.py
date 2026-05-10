from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from .ankiconnect import AnkiConnectClient
from .api_query import resolve_random_query
from .cache import JsonCardCache
from .config import Settings, get_settings
from .service import CardService, scheduler_loop


logger = logging.getLogger(__name__)


def build_service(settings: Settings) -> CardService:
    client = AnkiConnectClient(
        settings.ankiconnect_url,
        settings.ankiconnect_timeout_seconds,
        settings.ankiconnect_api_key,
    )
    cache = JsonCardCache(
        settings.cache_path,
        default_query=settings.card_query,
        max_cached_queries=settings.max_cached_queries,
    )
    return CardService(settings, client, cache)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    service = build_service(settings)
    app.state.settings = settings
    app.state.service = service
    task: asyncio.Task | None = None
    service.register_default_query()
    if settings.refresh_on_startup:
        try:
            await service.refresh_from_anki(trigger_sync=False)
        except Exception:
            logger.exception("startup refresh failed; serving existing cache")
    if settings.background_sync_enabled:
        task = asyncio.create_task(scheduler_loop(service))
    try:
        yield
    finally:
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        await service.client.aclose()


app = FastAPI(
    title="TRMNL Anki",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/api/random")
def random_card(
    query: str | None = None,
    deck: str | None = None,
    filter: str | None = None,
) -> dict:
    settings = app.state.settings
    request = resolve_random_query(
        query=query,
        deck=deck,
        filter=filter,
        default_query=settings.card_query,
        default_cadence_minutes=settings.cadence_minutes,
        max_query_length=settings.max_query_length,
    )
    return app.state.service.random(request=request)

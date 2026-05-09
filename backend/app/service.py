from __future__ import annotations

from datetime import datetime, timedelta, timezone
import asyncio
import logging

from .ankiconnect import AnkiConnectClient
from .api_query import QuerySpec, resolve_current_query
from .cache import JsonCardCache, utc_now_iso
from .config import Settings
from .normalize import normalize_cards
from .rotation import card_for_slot, slot_id_for


logger = logging.getLogger(__name__)


class CardService:
    def __init__(self, settings: Settings, client: AnkiConnectClient, cache: JsonCardCache) -> None:
        self.settings = settings
        self.client = client
        self.cache = cache
        self._refresh_lock = asyncio.Lock()
        self._sync_lock = asyncio.Lock()
        self.default_spec = resolve_current_query(
            default_query=settings.card_query,
            cadence_minutes=settings.cadence_minutes,
            default_cadence_minutes=settings.cadence_minutes,
            max_query_length=settings.max_query_length,
        )

    def register_default_query(self) -> dict:
        return self.cache.register_pending(self.default_spec)

    async def sync_ankiweb(self) -> tuple[bool, str | None]:
        async with self._sync_lock:
            try:
                await self.client.sync(timeout_seconds=self.settings.ankiconnect_sync_timeout_seconds)
            except Exception as exc:
                logger.warning("Anki sync failed; trying local card extraction anyway: %s", exc)
                return False, str(exc)
            return True, None

    async def refresh_from_anki(self, *, trigger_sync: bool = False) -> dict:
        return await self.refresh_query(self.default_spec, trigger_sync=trigger_sync)

    async def refresh_query(self, spec: QuerySpec, *, trigger_sync: bool = False) -> dict:
        async with self._refresh_lock:
            sync_error: str | None = None
            if trigger_sync:
                _, sync_error = await self.sync_ankiweb()
            try:
                card_ids = await self.client.find_cards(spec.effective_query)
                if spec.query_label == "default" and len(card_ids) < self.settings.min_cards:
                    card_ids = await self.client.find_cards(self.settings.fallback_query)
                card_ids = card_ids[: self.settings.max_cards]
                raw_cards = await self.client.cards_info(card_ids)
                cards, skipped = normalize_cards(raw_cards)
                result = self.cache.update_entry_success(spec, cards, included=len(cards), skipped=skipped)
                if sync_error is not None:
                    result = self.cache.mark_entry_stale(
                        spec,
                        f"sync failed before successful local extraction: {sync_error}",
                        retry_seconds=self.settings.sync_retry_interval_seconds,
                    )
                return result
            except Exception as exc:
                try:
                    return self.cache.update_entry_failure(
                        spec,
                        str(exc),
                        retry_seconds=self.settings.sync_retry_interval_seconds,
                    )
                except Exception:
                    return self.cache.load()

    async def refresh_due_entries(self, *, now: datetime | None = None) -> list[dict]:
        refreshed = []
        for entry in self.cache.due_entries(now=now):
            spec = QuerySpec(
                effective_query=entry["effective_query"],
                query_key=entry["query_key"],
                query_label=entry.get("query_label") or "custom",
                cadence_minutes=entry.get("cadence_minutes") or self.settings.cadence_minutes,
            )
            refreshed.append(await self.refresh_query(spec, trigger_sync=False))
        return refreshed

    def current(self, now: datetime | None = None, *, request: QuerySpec | None = None) -> dict:
        spec = request or self.default_spec
        now = now or datetime.now(timezone.utc)
        self.cache.register_pending(spec, now=now)
        cache = self.cache.load()
        entry = self.cache.entry_for(spec.query_key, data=cache) or {}
        cadence_minutes = entry.get("cadence_minutes") or spec.cadence_minutes
        cards = entry.get("cards") or []
        slot_id = slot_id_for(now, cadence_minutes)
        card = card_for_slot(cards, slot_id)
        sync_status = entry.get("last_sync_status")
        status = "ok" if card else "empty"
        if not card and sync_status in ("pending", "never", None):
            status = "not_ready"
        elif not card and sync_status not in ("never", None):
            status = "error"
        stale = sync_status not in ("ok", "never", None)
        return {
            "schema_version": cache.get("schema_version", 2),
            "status": status,
            "generated_at": utc_now_iso(),
            "last_sync_at": entry.get("last_sync_at"),
            "last_success_at": entry.get("last_success_at"),
            "last_sync_status": sync_status,
            "last_sync_error": entry.get("last_sync_error"),
            "error": entry.get("last_sync_error"),
            "slot_id": slot_id,
            "cadence_minutes": cadence_minutes,
            "stale": bool(stale),
            "card": card,
            "query_key": spec.query_key,
            "query_label": spec.query_label,
            "next_refresh_at": entry.get("next_due_at"),
        }


async def scheduler_loop(service: CardService) -> None:
    settings = service.settings
    next_global_sync_at = datetime.now(timezone.utc)
    while True:
        now = datetime.now(timezone.utc)
        await service.refresh_due_entries(now=now)
        if now >= next_global_sync_at:
            ok, _ = await service.sync_ankiweb()
            interval = settings.sync_interval_seconds if ok else settings.sync_retry_interval_seconds
            next_global_sync_at = now + timedelta(seconds=interval)
        await asyncio.sleep(min(30, settings.sync_retry_interval_seconds))

from __future__ import annotations

from datetime import datetime, timezone
import asyncio

from .ankiconnect import AnkiConnectClient
from .cache import JsonCardCache, utc_now_iso
from .config import Settings
from .normalize import normalize_cards
from .rotation import card_for_slot, slot_id_for


class CardService:
    def __init__(self, settings: Settings, client: AnkiConnectClient, cache: JsonCardCache) -> None:
        self.settings = settings
        self.client = client
        self.cache = cache
        self._refresh_lock = asyncio.Lock()

    async def refresh_from_anki(self, *, trigger_sync: bool = False) -> dict:
        async with self._refresh_lock:
            try:
                if trigger_sync:
                    await self.client.sync()
                card_ids = await self.client.find_cards(self.settings.card_query)
                if len(card_ids) < self.settings.min_cards:
                    card_ids = await self.client.find_cards(self.settings.fallback_query)
                card_ids = card_ids[: self.settings.max_cards]
                raw_cards = await self.client.cards_info(card_ids)
                cards, skipped = normalize_cards(raw_cards)
                return self.cache.update_success(cards, included=len(cards), skipped=skipped)
            except Exception as exc:
                try:
                    return self.cache.update_failure(str(exc))
                except Exception:
                    return self.cache.load()

    def current(self, now: datetime | None = None) -> dict:
        now = now or datetime.now(timezone.utc)
        cache = self.cache.load()
        cards = cache.get("cards") or []
        slot_id = slot_id_for(now, self.settings.cadence_minutes)
        card = card_for_slot(cards, slot_id)
        status = "ok" if card else "empty"
        stale = cache.get("last_sync_status") != "ok"
        return {
            "schema_version": cache.get("schema_version", 1),
            "status": status if not stale or card else "error",
            "generated_at": utc_now_iso(),
            "last_sync_at": cache.get("last_sync_at"),
            "last_success_at": cache.get("last_success_at"),
            "last_sync_status": cache.get("last_sync_status"),
            "last_sync_error": cache.get("last_sync_error"),
            "error": cache.get("last_sync_error"),
            "slot_id": slot_id,
            "cadence_minutes": self.settings.cadence_minutes,
            "stale": bool(stale),
            "card": card,
        }

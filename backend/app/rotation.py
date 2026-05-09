from __future__ import annotations

from datetime import datetime, timezone


def slot_id_for(now: datetime, cadence_minutes: int) -> int:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return int(now.timestamp()) // (cadence_minutes * 60)


def card_for_slot(cards: list[dict], slot_id: int) -> dict | None:
    if not cards:
        return None
    return cards[slot_id % len(cards)]

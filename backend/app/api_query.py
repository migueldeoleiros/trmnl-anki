from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from fastapi import HTTPException


ALLOWED_CADENCE_MINUTES = {15, 30, 60}
DEFAULT_CADENCE_MINUTES = 30
DEFAULT_MAX_QUERY_LENGTH = 500
QUERY_KEY_SCHEMA_VERSION = 2
SELECTED_FIELD_CONTRACT = "selected-fields:v2"


@dataclass(frozen=True)
class QuerySpec:
    effective_query: str
    query_key: str
    query_label: str
    cadence_minutes: int


def query_key_for(effective_query: str, *, cadence_minutes: int | None = None) -> str:
    del cadence_minutes  # Cadence controls refresh timing, not cache identity.
    normalized_query = " ".join(effective_query.strip().split())
    payload = f"schema={QUERY_KEY_SCHEMA_VERSION}\nquery={normalized_query}\nfields={SELECTED_FIELD_CONTRACT}"
    return sha256(payload.encode("utf-8")).hexdigest()[:24]


def resolve_random_query(
    *,
    query: str | None = None,
    deck: str | None = None,
    filter: str | None = None,
    default_cadence_minutes: int = DEFAULT_CADENCE_MINUTES,
    default_query: str,
    max_query_length: int = DEFAULT_MAX_QUERY_LENGTH,
) -> QuerySpec:
    has_query = query is not None
    has_deck_or_filter = deck is not None or filter is not None
    if has_query and has_deck_or_filter:
        raise HTTPException(status_code=400, detail="query cannot be mixed with deck or filter")

    if has_query:
        effective_query = (query or "").strip()
        if not effective_query:
            raise HTTPException(status_code=400, detail="query must not be empty")
        query_label = "custom"
    elif has_deck_or_filter:
        deck_name = (deck or "").strip()
        if not deck_name:
            raise HTTPException(status_code=400, detail="deck must not be empty when using deck/filter params")
        effective_query = f'deck:"{_escape_deck_name(deck_name)}"'
        filter_text = (filter or "").strip()
        if filter_text:
            effective_query = f"{effective_query} ({filter_text})"
        query_label = deck_name
    else:
        effective_query = default_query.strip()
        query_label = "default"

    if len(effective_query) > max_query_length:
        raise HTTPException(status_code=400, detail=f"query must be {max_query_length} characters or fewer")

    return QuerySpec(
        effective_query=effective_query,
        query_key=query_key_for(effective_query),
        query_label=query_label,
        cadence_minutes=default_cadence_minutes,
    )


def _escape_deck_name(deck_name: str) -> str:
    return deck_name.replace("\\", "\\\\").replace('"', '\\"')

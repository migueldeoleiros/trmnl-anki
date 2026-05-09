from __future__ import annotations

import json

import pytest
from fastapi import HTTPException


def test_deck_and_filter_params_compose_quoted_anki_search_with_escaped_deck_name():
    from app.api_query import resolve_current_query

    resolved = resolve_current_query(deck='Core "2k"', filter="is:review", default_query='deck:"Core 2000"')

    assert resolved.effective_query == 'deck:"Core \\"2k\\"" (is:review)'
    assert resolved.query_label == 'Core "2k"'


def test_raw_query_must_not_mix_with_deck_or_filter():
    from app.api_query import resolve_current_query

    with pytest.raises(HTTPException) as exc_info:
        resolve_current_query(query='deck:"Core 2000"', deck="Core 2000", default_query='deck:"Core 2000"')

    assert exc_info.value.status_code == 400


def test_empty_and_overlong_raw_queries_are_rejected():
    from app.api_query import resolve_current_query

    with pytest.raises(HTTPException) as empty_exc:
        resolve_current_query(query="   ", default_query='deck:"Core 2000"')
    with pytest.raises(HTTPException) as long_exc:
        resolve_current_query(query="x" * 501, default_query='deck:"Core 2000"')

    assert empty_exc.value.status_code == 400
    assert long_exc.value.status_code == 400


def test_query_key_is_stable_and_ignores_cadence():
    from app.api_query import query_key_for

    query = 'deck:"Core 2000" (is:learn or is:review)'

    assert query_key_for(query, cadence_minutes=15) == query_key_for(query, cadence_minutes=60)
    assert query_key_for(query, cadence_minutes=30) != query_key_for('deck:"Core 2000" is:review', cadence_minutes=30)


def test_cadence_minutes_allows_only_contract_values():
    from app.api_query import resolve_current_query

    for cadence in (15, 30, 60):
        assert resolve_current_query(default_query='deck:"Core 2000"', cadence_minutes=cadence).cadence_minutes == cadence

    with pytest.raises(HTTPException) as exc_info:
        resolve_current_query(default_query='deck:"Core 2000"', cadence_minutes=45)

    assert exc_info.value.status_code == 400


def test_current_request_path_is_cache_only_for_cold_custom_query(tmp_path):
    from app.api_query import resolve_current_query
    from app.cache import JsonCardCache
    from app.config import Settings
    from app.service import CardService

    class ExplodingClient:
        async def find_cards(self, query):  # pragma: no cover - should never be called by current()
            raise AssertionError("current() must not call AnkiConnect")

    settings = Settings(cache_path=tmp_path / "cards.json", cadence_minutes=30)
    service = CardService(settings, client=ExplodingClient(), cache=JsonCardCache(settings.cache_path))  # type: ignore[arg-type]
    request = resolve_current_query(query='deck:"Core 2000" is:review', default_query=settings.card_query)

    payload = service.current(request=request)

    assert payload["status"] == "not_ready"
    assert payload["card"] is None
    assert payload["query_key"] == request.query_key


def test_cold_not_ready_fixture_matches_response_contract():
    fixture = json.loads(open("fixtures/current-not-ready.json", encoding="utf-8").read())

    assert fixture["status"] == "not_ready"
    assert fixture["card"] is None
    assert fixture["query_key"]
    assert fixture["query_label"] == "custom"
    assert "query" not in fixture
    assert fixture["next_refresh_at"] is not None

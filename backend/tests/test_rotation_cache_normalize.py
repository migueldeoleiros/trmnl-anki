from datetime import datetime, timezone

from app.ankiconnect import AnkiConnectClient
from app.cache import JsonCardCache
from app.config import Settings
from app.normalize import furigana_to_html, normalize_card, reading_text
from app.rotation import card_for_slot, slot_id_for
from app.service import CardService


def test_slot_rotation_is_stable_within_slot_and_changes_next_slot():
    cards = [{"headword": "a"}, {"headword": "b"}]
    first = datetime(2026, 5, 9, 12, 0, 1, tzinfo=timezone.utc)
    same_slot = datetime(2026, 5, 9, 12, 29, 59, tzinfo=timezone.utc)
    next_slot = datetime(2026, 5, 9, 12, 30, 0, tzinfo=timezone.utc)

    first_slot = slot_id_for(first, 30)
    assert slot_id_for(same_slot, 30) == first_slot
    assert slot_id_for(next_slot, 30) == first_slot + 1
    assert card_for_slot(cards, first_slot) == card_for_slot(cards, slot_id_for(same_slot, 30))
    assert card_for_slot(cards, first_slot) != card_for_slot(cards, slot_id_for(next_slot, 30))


def test_normalize_card_uses_approved_field_fallbacks_and_ruby():
    raw = {
        "cardId": 123,
        "deckName": "Core 2000",
        "fields": {
            "Expression": {"value": "言葉"},
            "Vocabulary-Furigana": {"value": "言葉[ことば]"},
            "Vocabulary-English": {"value": "word"},
            "Sentence-Kana": {"value": "いい言葉です"},
            "Sentence-English": {"value": "It is a good word."},
        },
    }

    card = normalize_card(raw)

    assert card["headword"] == "言葉"
    assert card["meaning"] == "word"
    assert card["reading"] == "ことば"
    assert card["furigana_html"] == "<ruby>言葉<rt>ことば</rt></ruby>"
    assert card["sentence_translation"] == "It is a good word."


def test_cache_preserves_cards_after_failed_refresh(tmp_path):
    cache = JsonCardCache(tmp_path / "cards.json")
    cache.update_success([{"headword": "一", "meaning": "one"}], included=1, skipped=0)
    failed = cache.update_failure("anki offline")

    assert failed["cards"] == [{"headword": "一", "meaning": "one"}]
    assert failed["last_sync_status"] == "error"


def test_current_marks_stale_but_returns_cached_card(tmp_path):
    settings = Settings(cache_path=tmp_path / "cards.json", cadence_minutes=30)
    cache = JsonCardCache(settings.cache_path)
    cache.update_success([{"headword": "一", "meaning": "one"}], included=1, skipped=0)
    cache.update_failure("anki offline")
    service = CardService(settings, client=None, cache=cache)  # type: ignore[arg-type]

    payload = service.current(datetime(2026, 5, 9, 12, 0, tzinfo=timezone.utc))

    assert payload["status"] == "ok"
    assert payload["stale"] is True
    assert payload["card"] == {"headword": "一", "meaning": "one"}


def test_existing_ruby_html_is_preserved_without_unsafe_tags():
    raw = '<ruby class="x">朝食<rt>ちょうしょく</rt></ruby><script>alert(1)</script>'

    assert furigana_to_html(raw) == "<ruby>朝食<rt>ちょうしょく</rt></ruby>"


def test_cache_corruption_returns_error_state(tmp_path):
    cache_path = tmp_path / "cards.json"
    cache_path.write_text("{not json", encoding="utf-8")

    data = JsonCardCache(cache_path).load()

    assert data["cards"] == []
    assert data["last_sync_status"] == "error"
    assert "cache read failed" in data["last_sync_error"]
    assert not cache_path.exists()
    assert cache_path.with_suffix(".json.corrupt").exists()


def test_empty_refresh_preserves_existing_cards(tmp_path):
    cache = JsonCardCache(tmp_path / "cards.json")
    cache.update_success([{"headword": "一", "meaning": "one"}], included=1, skipped=0)

    data = cache.update_success([], included=0, skipped=4)

    assert data["cards"] == [{"headword": "一", "meaning": "one"}]
    assert data["last_sync_status"] == "error"
    assert "no usable cards" in data["last_sync_error"]


def test_first_empty_refresh_is_error_for_retry_loop(tmp_path):
    cache = JsonCardCache(tmp_path / "cards.json")

    data = cache.update_success([], included=0, skipped=4)

    assert data["cards"] == []
    assert data["last_sync_status"] == "error"
    assert "no usable cards" in data["last_sync_error"]


def test_reading_text_extracts_bracket_reading():
    assert reading_text("朝食[ちょうしょく]") == "ちょうしょく"


def test_plain_fields_escape_encoded_html():
    raw = {
        "cardId": 123,
        "deckName": "Core 2000",
        "fields": {
            "Expression": {"value": "&lt;script&gt;alert(1)&lt;/script&gt;言葉"},
            "Vocabulary-English": {"value": "&lt;b&gt;word&lt;/b&gt;"},
        },
    }

    card = normalize_card(raw)

    assert card["headword"] == "alert(1)言葉"
    assert card["meaning"] == "word"


def test_ankiconnect_client_includes_api_key(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"result": 6, "error": None}

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout
            self.closed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

        async def aclose(self):
            self.closed = True

    monkeypatch.setattr("app.ankiconnect.httpx.AsyncClient", FakeAsyncClient)

    import asyncio

    result = asyncio.run(AnkiConnectClient("http://anki:8765", api_key="secret").version())

    assert result == 6
    assert captured["json"]["key"] == "secret"


def test_cache_save_uses_unique_temp_names(tmp_path, monkeypatch):
    names = []
    original_replace = __import__("app.cache", fromlist=["os"]).os.replace

    def capture_replace(src, dst):
        names.append(src)
        original_replace(src, dst)

    monkeypatch.setattr("app.cache.os.replace", capture_replace)
    cache = JsonCardCache(tmp_path / "cards.json")

    cache.update_success([{"headword": "一", "meaning": "one"}], included=1, skipped=0)
    cache.update_failure("anki offline")

    assert len(names) == 2
    assert names[0] != names[1]


def test_mark_stale_preserves_successful_local_extraction(tmp_path):
    cache = JsonCardCache(tmp_path / "cards.json")
    cache.update_success([{"headword": "一", "meaning": "one"}], included=1, skipped=0)

    data = cache.mark_stale("sync failed before successful local extraction")

    assert data["cards"] == [{"headword": "一", "meaning": "one"}]
    assert data["last_sync_status"] == "error"
    assert "sync failed" in data["last_sync_error"]


def test_current_empty_cache_uses_empty_status(tmp_path):
    settings = Settings(cache_path=tmp_path / "cards.json", cadence_minutes=30)
    service = CardService(settings, client=None, cache=JsonCardCache(settings.cache_path))  # type: ignore[arg-type]

    payload = service.current(datetime(2026, 5, 9, 12, 0, tzinfo=timezone.utc))

    assert payload["status"] == "empty"
    assert payload["stale"] is False
    assert payload["error"] is None

from __future__ import annotations

import html
import re
from typing import Any


FIELD_ORDER = {
    "headword": ("Vocabulary-Kanji", "Expression", "Vocabulary-Kana"),
    "furigana": ("Vocabulary-Furigana", "Reading", "Vocabulary-Kana"),
    "meaning": ("Vocabulary-English",),
    "sentence": ("Sentence-Kana",),
    "sentence_translation": ("Sentence-English",),
}

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_UNSAFE_BLOCK_RE = re.compile(r"<\s*(script|style)[^>]*>.*?<\s*/\s*\1\s*>", re.IGNORECASE | re.DOTALL)
_ALLOWED_TAG_RE = re.compile(r"</?(ruby|rt|rp|rb|br)\b[^>]*>", re.IGNORECASE)
_FURIGANA_RE = re.compile(r" ?([^\s\[]+)\[([^\]]+)\]")


def _field_value(fields: dict[str, Any], names: tuple[str, ...]) -> str:
    for name in names:
        value = fields.get(name)
        if isinstance(value, dict):
            text = value.get("value") or value.get("text") or ""
        else:
            text = value or ""
        text = str(text).strip()
        if text:
            return text
    return ""


def _plain_text(value: str) -> str:
    value = html.unescape(value)
    value = _HTML_TAG_RE.sub("", value)
    return html.escape(value, quote=False).strip()


def _sanitize_ruby_html(value: str) -> str:
    value = _UNSAFE_BLOCK_RE.sub("", value)
    placeholders: list[str] = []

    def keep_allowed(match: re.Match[str]) -> str:
        token = f"@@TAG{len(placeholders)}@@"
        tag = match.group(0)
        tag_match = re.match(r"</?\s*([a-z0-9]+)", tag, re.IGNORECASE)
        tag_name = tag_match.group(1).lower() if tag_match else ""
        if tag_name == "br":
            placeholders.append("<br>")
        elif tag.startswith("</"):
            placeholders.append(f"</{tag_name}>")
        else:
            placeholders.append(f"<{tag_name}>")
        return token

    escaped = html.escape(_ALLOWED_TAG_RE.sub(keep_allowed, value))
    for index, tag in enumerate(placeholders):
        escaped = escaped.replace(f"@@TAG{index}@@", tag)
    return escaped.strip()


def furigana_to_html(value: str) -> str:
    if "<ruby" in value.lower() and "<rt" in value.lower():
        return _sanitize_ruby_html(value)

    escaped = html.escape(_plain_text(value))

    def replace(match: re.Match[str]) -> str:
        base = html.escape(match.group(1))
        reading = html.escape(match.group(2))
        return f"<ruby>{base}<rt>{reading}</rt></ruby>"

    converted = _FURIGANA_RE.sub(replace, escaped)
    return converted or escaped


def reading_text(value: str) -> str:
    plain = _plain_text(value)
    readings = [match.group(2) for match in _FURIGANA_RE.finditer(plain)]
    if readings:
        return "".join(readings)
    return plain


def normalize_card(card: dict[str, Any]) -> dict[str, Any] | None:
    fields = card.get("fields") or {}
    headword_raw = _field_value(fields, FIELD_ORDER["headword"])
    meaning_raw = _field_value(fields, FIELD_ORDER["meaning"])
    if not headword_raw or not meaning_raw:
        return None

    furigana_raw = _field_value(fields, FIELD_ORDER["furigana"])
    normalized = {
        "card_id": card.get("cardId") or card.get("card_id"),
        "note_id": card.get("note") or card.get("noteId") or card.get("note_id"),
        "deck_name": card.get("deckName") or card.get("deck_name"),
        "model_name": card.get("modelName") or card.get("model_name"),
        "headword": _plain_text(headword_raw),
        "reading": reading_text(furigana_raw),
        "furigana_html": furigana_to_html(furigana_raw or headword_raw),
        "meaning": _plain_text(meaning_raw),
        "sentence": _plain_text(_field_value(fields, FIELD_ORDER["sentence"])),
        "sentence_translation": _plain_text(_field_value(fields, FIELD_ORDER["sentence_translation"])),
    }
    return normalized


def normalize_cards(cards: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    normalized: list[dict[str, Any]] = []
    skipped = 0
    seen: set[Any] = set()
    for card in cards:
        item = normalize_card(card)
        if not item:
            skipped += 1
            continue
        key = item.get("card_id") or (item["headword"], item["meaning"])
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    return normalized, skipped

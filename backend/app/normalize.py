from __future__ import annotations

import html
import re
from typing import Any


FIELD_ORDER = {
    "headword": ("Vocabulary-Kanji", "Vocabulary-Kana"),
    "furigana": ("Vocabulary-Furigana", "Vocabulary-Kana"),
    "meaning": ("Vocabulary-English",),
    "sentence": ("Expression", "Sentence-Kana"),
    "sentence_furigana": ("Sentence-Furigana", "Expression", "Sentence-Kana"),
    "sentence_reading": ("Reading", "Sentence-Reading", "Sentence-Kana"),
    "sentence_translation": ("Sentence-English",),
}

SELECTED_FIELD_NAMES = (
    "Vocabulary-Kanji",
    "Vocabulary-Furigana",
    "Vocabulary-Kana",
    "Vocabulary-English",
    "Expression",
    "Reading",
    "Sentence-Furigana",
    "Sentence-Reading",
    "Sentence-Kana",
    "Sentence-English",
)

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_UNSAFE_BLOCK_RE = re.compile(r"<\s*(script|style)[^>]*>.*?<\s*/\s*\1\s*>", re.IGNORECASE | re.DOTALL)
_UNSAFE_SINGLE_TAG_RE = re.compile(r"<\s*(img|a|iframe|object|embed|audio|video|source)\b[^>]*>", re.IGNORECASE)
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
    value = _UNSAFE_BLOCK_RE.sub("", value)
    value = _UNSAFE_SINGLE_TAG_RE.sub("", value)
    value = _HTML_TAG_RE.sub("", value)
    return html.escape(value, quote=False).strip()


def _sanitize_ruby_html(value: str) -> str:
    value = _UNSAFE_BLOCK_RE.sub("", value)
    value = _UNSAFE_SINGLE_TAG_RE.sub("", value)
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
    if _FURIGANA_RE.search(plain):
        return _FURIGANA_RE.sub(lambda match: match.group(2), plain)
    return plain


def sentence_to_ruby_html(sentence: str, reading: str) -> str:
    sentence_text = _plain_text(sentence)
    reading_text_value = _plain_text(reading)
    if not sentence_text or not reading_text_value:
        return furigana_to_html(sentence_text)

    parts: list[str] = []
    read_index = 0
    index = 0
    while index < len(sentence_text):
        char = sentence_text[index]
        if _is_cjk(char):
            start = index
            while index < len(sentence_text) and _is_cjk(sentence_text[index]):
                index += 1
            kanji = sentence_text[start:index]
            next_literal = _next_literal_run(sentence_text, index)
            if next_literal:
                next_index = _find_normalized(reading_text_value, next_literal, read_index)
                if next_index is None:
                    return furigana_to_html(sentence_text)
                ruby_reading = reading_text_value[read_index:next_index]
                read_index = next_index
            else:
                ruby_reading = reading_text_value[read_index:]
                read_index = len(reading_text_value)
            if ruby_reading:
                parts.append(f"<ruby>{html.escape(kanji)}<rt>{html.escape(ruby_reading)}</rt></ruby>")
            else:
                parts.append(html.escape(kanji))
            continue

        if read_index < len(reading_text_value) and _same_kana_or_literal(char, reading_text_value[read_index]):
            read_index += 1
        parts.append(html.escape(char))
        index += 1
    return "".join(parts)


def _selected_fields(fields: dict[str, Any]) -> dict[str, str]:
    selected: dict[str, str] = {}
    for name in SELECTED_FIELD_NAMES:
        value = _field_value(fields, (name,))
        if value:
            selected[name] = _plain_text(value)
    return selected


def _sentence_furigana_html(fields: dict[str, Any]) -> str:
    explicit = _field_value(fields, ("Sentence-Furigana",))
    if explicit:
        return furigana_to_html(explicit)
    reading = _field_value(fields, FIELD_ORDER["sentence_reading"])
    if _FURIGANA_RE.search(_plain_text(reading)):
        return furigana_to_html(reading)
    sentence = _field_value(fields, FIELD_ORDER["sentence"])
    return sentence_to_ruby_html(sentence, reading)


def _is_cjk(char: str) -> bool:
    return "\u3400" <= char <= "\u9fff" or "\uf900" <= char <= "\ufaff"


def _is_kana(char: str) -> bool:
    return "\u3040" <= char <= "\u30ff"


def _next_literal_run(value: str, start: int) -> str:
    run: list[str] = []
    for char in value[start:]:
        if _is_cjk(char):
            break
        if _is_kana(char):
            run.append(char)
            continue
        if run:
            break
    return "".join(run)


def _find_normalized(haystack: str, needle: str, start: int) -> int | None:
    normalized_haystack = _kana_to_hiragana(haystack)
    normalized_needle = _kana_to_hiragana(needle)
    index = normalized_haystack.find(normalized_needle, start)
    if index == -1:
        return None
    return index


def _same_kana_or_literal(left: str, right: str) -> bool:
    if _is_kana(left) or _is_kana(right):
        return _kana_to_hiragana(left) == _kana_to_hiragana(right)
    return left == right


def _kana_to_hiragana(value: str) -> str:
    chars = []
    for char in value:
        codepoint = ord(char)
        if 0x30A1 <= codepoint <= 0x30F6:
            chars.append(chr(codepoint - 0x60))
        else:
            chars.append(char)
    return "".join(chars)


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
        "sentence_furigana_html": _sentence_furigana_html(fields),
        "sentence_reading": reading_text(_field_value(fields, FIELD_ORDER["sentence_reading"])),
        "sentence_translation": _plain_text(_field_value(fields, FIELD_ORDER["sentence_translation"])),
        "fields": _selected_fields(fields),
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

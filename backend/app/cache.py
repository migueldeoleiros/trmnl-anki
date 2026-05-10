from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .api_query import QuerySpec, query_key_for


SCHEMA_VERSION = 2
LEGACY_SCHEMA_VERSION = 1


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class JsonCardCache:
    def __init__(self, path: Path, *, default_query: str | None = None, max_cached_queries: int = 25) -> None:
        self.path = path
        self.default_query = default_query or 'deck:"Core 2000" (is:learn or is:review)'
        self.default_query_key = query_key_for(self.default_query)
        self.max_cached_queries = max_cached_queries

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self.empty()
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            data = self.empty()
            timestamp = utc_now_iso()
            spec = self._default_spec()
            data["entries"][spec.query_key] = {
                **self._empty_entry(spec, timestamp),
                "last_sync_status": "error",
                "last_sync_error": f"cache read failed: {exc}",
            }
            self._quarantine_corrupt_cache()
            return data
        if self._is_v2(data):
            return {**self.empty(), **data}
        return self._migrate_v1(data)

    def _quarantine_corrupt_cache(self) -> None:
        if not self.path.exists():
            return
        corrupt_path = self.path.with_suffix(self.path.suffix + ".corrupt")
        try:
            shutil.move(str(self.path), str(corrupt_path))
        except OSError:
            pass

    def save(self, data: dict[str, Any]) -> None:
        if not self._is_v2(data):
            data = self._migrate_v1(data, save=False)
        self._evict_entries(data, protected_key=data.pop("_protected_query_key", None))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp_path, self.path)

    def register_pending(self, spec: QuerySpec, *, now: datetime | None = None) -> dict[str, Any]:
        timestamp = _iso(now)
        data = self.load()
        entries = data.setdefault("entries", {})
        entry = entries.get(spec.query_key)
        if entry is None:
            entry = self._empty_entry(spec, timestamp)
            entries[spec.query_key] = entry
        entry["query_key"] = spec.query_key
        entry["query_label"] = spec.query_label
        entry["effective_query"] = spec.effective_query
        entry["cadence_minutes"] = min(entry.get("cadence_minutes") or spec.cadence_minutes, spec.cadence_minutes)
        entry.setdefault("first_seen_at", timestamp)
        entry.setdefault("next_due_at", timestamp)
        entry["last_accessed_at"] = timestamp
        data["_protected_query_key"] = spec.query_key
        self.save(data)
        return self.load()

    def touch(self, spec: QuerySpec, *, now: datetime | None = None) -> dict[str, Any]:
        data = self.register_pending(spec, now=now)
        entry = (data.get("entries") or {}).get(spec.query_key)
        if entry is not None:
            entry["last_accessed_at"] = _iso(now)
            self.save(data)
        return self.load()

    def entry_for(self, query_key: str, *, data: dict[str, Any] | None = None) -> dict[str, Any] | None:
        source = data or self.load()
        entry = (source.get("entries") or {}).get(query_key)
        if entry is None:
            return None
        return {**self._entry_defaults(), **entry}

    def update_entry_success(
        self,
        spec: QuerySpec,
        cards: list[dict[str, Any]],
        *,
        included: int,
        skipped: int,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        timestamp = _iso(now)
        data = self.load()
        entry = self._ensure_entry(data, spec, timestamp)
        if included == 0:
            entry.update(
                {
                    "last_sync_at": timestamp,
                    "last_sync_status": "error",
                    "last_sync_error": "refresh produced no usable cards",
                    "included_count": 0,
                    "skipped_count": skipped,
                    "next_due_at": timestamp,
                }
            )
            self.save(data)
            return self.load()
        entry.update(
            {
                "cards": cards,
                "updated_at": timestamp,
                "last_sync_at": timestamp,
                "last_success_at": timestamp,
                "last_sync_status": "ok",
                "last_sync_error": None,
                "included_count": included,
                "skipped_count": skipped,
                "next_due_at": _iso(_parse_iso(timestamp) + timedelta(minutes=entry["cadence_minutes"])),
            }
        )
        self.save(data)
        return self.load()

    def update_entry_failure(
        self,
        spec: QuerySpec,
        error: str,
        *,
        now: datetime | None = None,
        retry_seconds: int | None = None,
        retry_interval_seconds: int | None = None,
    ) -> dict[str, Any]:
        timestamp = _iso(now)
        data = self.load()
        entry = self._ensure_entry(data, spec, timestamp)
        retry_delay = retry_seconds if retry_seconds is not None else retry_interval_seconds or 0
        next_due = _parse_iso(timestamp) + timedelta(seconds=retry_delay)
        entry.update(
            {
                "last_sync_at": timestamp,
                "last_sync_status": "error",
                "last_sync_error": error,
                "next_due_at": _iso(next_due),
            }
        )
        self.save(data)
        return self.load()

    def mark_entry_stale(
        self,
        spec: QuerySpec,
        error: str,
        *,
        now: datetime | None = None,
        retry_seconds: int | None = None,
        retry_interval_seconds: int | None = None,
    ) -> dict[str, Any]:
        return self.update_entry_failure(
            spec,
            error,
            now=now,
            retry_seconds=retry_seconds,
            retry_interval_seconds=retry_interval_seconds,
        )

    def due_entries(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        current = now or datetime.now(timezone.utc)
        due = []
        for entry in (self.load().get("entries") or {}).values():
            next_due_at = entry.get("next_due_at")
            if next_due_at is None or _parse_iso(next_due_at) <= current:
                due.append({**self._entry_defaults(), **entry})
        return sorted(due, key=lambda item: item.get("next_due_at") or "")

    @staticmethod
    def empty() -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "entries": {},
        }

    @staticmethod
    def _entry_defaults() -> dict[str, Any]:
        return {
            "cards": [],
            "updated_at": None,
            "last_sync_at": None,
            "last_success_at": None,
            "last_sync_status": "never",
            "last_sync_error": None,
            "included_count": 0,
            "skipped_count": 0,
            "first_seen_at": None,
            "last_accessed_at": None,
            "next_due_at": None,
            "cadence_minutes": 30,
        }

    def _default_spec(self) -> QuerySpec:
        return QuerySpec(
            effective_query=self.default_query,
            query_key=self.default_query_key,
            query_label="default",
            cadence_minutes=30,
        )

    def _empty_entry(self, spec: QuerySpec, timestamp: str) -> dict[str, Any]:
        return {
            **self._entry_defaults(),
            "query_key": spec.query_key,
            "query_label": spec.query_label,
            "effective_query": spec.effective_query,
            "cadence_minutes": spec.cadence_minutes,
            "last_sync_status": "pending",
            "first_seen_at": timestamp,
            "last_accessed_at": timestamp,
            "next_due_at": timestamp,
        }

    def _ensure_entry(self, data: dict[str, Any], spec: QuerySpec, timestamp: str) -> dict[str, Any]:
        entries = data.setdefault("entries", {})
        entry = entries.setdefault(spec.query_key, self._empty_entry(spec, timestamp))
        entry.update(
            {
                "query_key": spec.query_key,
                "query_label": spec.query_label,
                "effective_query": spec.effective_query,
                "cadence_minutes": min(entry.get("cadence_minutes") or spec.cadence_minutes, spec.cadence_minutes),
                "last_accessed_at": timestamp,
            }
        )
        return entry

    def _is_v2(self, data: dict[str, Any]) -> bool:
        return data.get("schema_version") == SCHEMA_VERSION and isinstance(data.get("entries"), dict)

    def _migrate_v1(self, data: dict[str, Any], *, save: bool = True) -> dict[str, Any]:
        migrated = self.empty()
        spec = self._default_spec()
        timestamp = utc_now_iso()
        migrated["entries"][spec.query_key] = {
            **self._empty_entry(spec, timestamp),
            "cards": data.get("cards") or [],
            "updated_at": data.get("updated_at"),
            "last_sync_at": data.get("last_sync_at"),
            "last_success_at": data.get("last_success_at"),
            "last_sync_status": data.get("last_sync_status", "never"),
            "last_sync_error": data.get("last_sync_error"),
            "included_count": data.get("included_count", 0),
            "skipped_count": data.get("skipped_count", 0),
        }
        if save and data.get("schema_version") == LEGACY_SCHEMA_VERSION:
            self.save(migrated)
        return migrated

    def _evict_entries(self, data: dict[str, Any], *, protected_key: str | None = None) -> None:
        entries = data.get("entries") or {}
        while len(entries) > self.max_cached_queries:
            candidates = [key for key in entries if key not in {self.default_query_key, protected_key}]
            if not candidates:
                candidates = [key for key in entries if key != self.default_query_key] or list(entries)
            victim = min(candidates, key=lambda key: (bool(entries[key].get("cards")), entries[key].get("last_accessed_at") or ""))
            del entries[victim]


def _iso(value: datetime | None) -> str:
    if value is None:
        return utc_now_iso()
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

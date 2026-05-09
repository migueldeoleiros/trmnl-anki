from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class JsonCardCache:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self.empty()
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            data = self.empty()
            data.update(
                {
                    "last_sync_status": "error",
                    "last_sync_error": f"cache read failed: {exc}",
                }
            )
            self._quarantine_corrupt_cache()
            return data
        return {**self.empty(), **data}

    def _quarantine_corrupt_cache(self) -> None:
        if not self.path.exists():
            return
        corrupt_path = self.path.with_suffix(self.path.suffix + ".corrupt")
        try:
            shutil.move(str(self.path), str(corrupt_path))
        except OSError:
            pass

    def save(self, data: dict[str, Any]) -> None:
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

    def update_success(self, cards: list[dict[str, Any]], *, included: int, skipped: int) -> dict[str, Any]:
        now = utc_now_iso()
        data = self.load()
        if included == 0:
            data.update(
                {
                    "schema_version": SCHEMA_VERSION,
                    "last_sync_at": now,
                    "last_sync_status": "error",
                    "last_sync_error": "refresh produced no usable cards",
                    "included_count": 0,
                    "skipped_count": skipped,
                }
            )
            self.save(data)
            return data
        data.update(
            {
                "schema_version": SCHEMA_VERSION,
                "cards": cards,
                "updated_at": now,
                "last_sync_at": now,
                "last_success_at": now,
                "last_sync_status": "ok",
                "last_sync_error": None,
                "included_count": included,
                "skipped_count": skipped,
            }
        )
        self.save(data)
        return data

    def update_failure(self, error: str) -> dict[str, Any]:
        data = self.load()
        data.update(
            {
                "schema_version": SCHEMA_VERSION,
                "last_sync_at": utc_now_iso(),
                "last_sync_status": "error",
                "last_sync_error": error,
            }
        )
        self.save(data)
        return data

    def mark_stale(self, error: str) -> dict[str, Any]:
        data = self.load()
        data.update(
            {
                "schema_version": SCHEMA_VERSION,
                "last_sync_at": utc_now_iso(),
                "last_sync_status": "error",
                "last_sync_error": error,
            }
        )
        self.save(data)
        return data

    @staticmethod
    def empty() -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "cards": [],
            "updated_at": None,
            "last_sync_at": None,
            "last_success_at": None,
            "last_sync_status": "never",
            "last_sync_error": None,
            "included_count": 0,
            "skipped_count": 0,
        }

from __future__ import annotations

from typing import Any

import httpx


class AnkiConnectError(RuntimeError):
    pass


class AnkiConnectClient:
    def __init__(self, base_url: str, timeout_seconds: float = 10.0, api_key: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=self.timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def invoke(self, action: str, params: dict[str, Any] | None = None) -> Any:
        payload = {"action": action, "version": 6, "params": params or {}}
        if self.api_key:
            payload["key"] = self.api_key
        response = await self._client.post(self.base_url, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("error") is not None:
            raise AnkiConnectError(f"{action} failed: {data['error']}")
        return data.get("result")

    async def invoke_with_timeout(self, action: str, timeout_seconds: float, params: dict[str, Any] | None = None) -> Any:
        payload = {"action": action, "version": 6, "params": params or {}}
        if self.api_key:
            payload["key"] = self.api_key
        response = await self._client.post(self.base_url, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
        data = response.json()
        if data.get("error") is not None:
            raise AnkiConnectError(f"{action} failed: {data['error']}")
        return data.get("result")

    async def version(self) -> int:
        return int(await self.invoke("version"))

    async def deck_names(self) -> list[str]:
        return list(await self.invoke("deckNames"))

    async def find_cards(self, query: str) -> list[int]:
        return list(await self.invoke("findCards", {"query": query}))

    async def cards_info(self, card_ids: list[int]) -> list[dict[str, Any]]:
        if not card_ids:
            return []
        return list(await self.invoke("cardsInfo", {"cards": card_ids}))

    async def cards_to_notes(self, card_ids: list[int]) -> list[int]:
        if not card_ids:
            return []
        return list(await self.invoke("cardsToNotes", {"cards": card_ids}))

    async def notes_info(self, note_ids: list[int]) -> list[dict[str, Any]]:
        if not note_ids:
            return []
        return list(await self.invoke("notesInfo", {"notes": note_ids}))

    async def sync(self, timeout_seconds: float | None = None) -> Any:
        if timeout_seconds is not None:
            return await self.invoke_with_timeout("sync", timeout_seconds)
        return await self.invoke("sync")

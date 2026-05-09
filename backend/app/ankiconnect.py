from __future__ import annotations

from typing import Any

import httpx


class AnkiConnectError(RuntimeError):
    pass


class AnkiConnectClient:
    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def invoke(self, action: str, params: dict[str, Any] | None = None) -> Any:
        payload = {"action": action, "version": 6, "params": params or {}}
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(self.base_url, json=payload)
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

    async def sync(self) -> Any:
        return await self.invoke("sync")

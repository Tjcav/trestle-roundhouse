from __future__ import annotations

from typing import Any

import httpx


from .interfaces import HAReadClient
from .models import HAEntity, HAState


class HAClient(HAReadClient):
    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def get_json(self, path: str) -> Any:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def get_config(self) -> Any:
        return await self.get_json("/api/config")

    async def get_states(self) -> dict[str, HAState]:
        raw_states = await self.get_json("/api/states")
        states: dict[str, HAState] = {}
        for item in raw_states or []:
            entity_id = item.get("entity_id")
            if not entity_id:
                continue
            states[entity_id] = HAState(
                entity_id=entity_id,
                state=item.get("state", ""),
                attributes=item.get("attributes", {}) or {},
            )
        return states

    async def list_entities(self) -> list[HAEntity]:
        states = await self.get_states()
        entities: list[HAEntity] = []
        for entity_id, state in states.items():
            domain = entity_id.split(".", 1)[0] if "." in entity_id else "unknown"
            name = state.attributes.get("friendly_name") if isinstance(state.attributes, dict) else None
            entities.append(HAEntity(entity_id=entity_id, domain=domain, name=name))
        return entities

    async def get_services(self) -> Any:
        return await self.get_json("/api/services")

    async def get_devices(self) -> Any:
        return await self.get_json("/api/device_registry")

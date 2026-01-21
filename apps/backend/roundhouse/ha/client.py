from __future__ import annotations

from typing import Any, cast

import httpx

from .interfaces import HAReadClient
from .models import HAEntity, HAState

type JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


class HAClient(HAReadClient):
    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def get_json(self, path: str) -> JsonValue:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, headers=self._headers())
            response.raise_for_status()
            return cast(JsonValue, response.json())

    async def get_config(self) -> JsonValue:
        return await self.get_json("/api/config")

    async def get_states(self) -> dict[str, HAState]:
        raw_states = await self.get_json("/api/states")
        states: dict[str, HAState] = {}
        if not isinstance(raw_states, list):
            return states
        for item in raw_states:
            if not isinstance(item, dict):
                continue
            item_data = cast(dict[str, Any], item)
            entity_id = item_data.get("entity_id")
            if not isinstance(entity_id, str) or not entity_id:
                continue
            state_raw = item_data.get("state")
            state = state_raw if isinstance(state_raw, str) else ""
            attributes_raw = item_data.get("attributes")
            if isinstance(attributes_raw, dict):
                attributes = cast(dict[str, Any], attributes_raw)
            else:
                attributes = {}
            states[entity_id] = HAState(
                entity_id=entity_id,
                state=state,
                attributes=attributes,
            )
        return states

    async def list_entities(self) -> list[HAEntity]:
        states = await self.get_states()
        entities: list[HAEntity] = []
        for entity_id, state in states.items():
            domain = entity_id.split(".", 1)[0] if "." in entity_id else "unknown"
            name = state.attributes.get("friendly_name")
            if not isinstance(name, str):
                name = None
            entities.append(HAEntity(entity_id=entity_id, domain=domain, name=name))
        return entities

    async def get_services(self) -> JsonValue:
        return await self.get_json("/api/services")

    async def get_devices(self) -> JsonValue:
        return await self.get_json("/api/device_registry")

from __future__ import annotations

from roundhouse.ha.interfaces import HAReadClient
from roundhouse.trestle_bridge.interfaces import TrestleExecutor


class EnvironmentService:
    def __init__(self, ha: HAReadClient | None, trestle: TrestleExecutor | None) -> None:
        self._ha = ha
        self._trestle = trestle

    async def get_environment_status(self) -> dict:
        # Returns domain objects; routes serialize for HTTP.
        if not self._ha:
            return {"ha_available": False, "entities": []}
        entities = await self._ha.list_entities()
        return {"ha_available": True, "entities": entities}

    async def get_states(self) -> dict:
        if not self._ha:
            return {"ha_available": False, "states": {}}
        states = await self._ha.get_states()
        return {"ha_available": True, "states": states}

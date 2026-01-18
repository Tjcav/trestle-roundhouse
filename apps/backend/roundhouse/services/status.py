from __future__ import annotations

from roundhouse.ha.interfaces import HAReadClient
from roundhouse.trestle_bridge.interfaces import TrestleExecutor


class StatusService:
    def __init__(self, ha: HAReadClient | None, trestle: TrestleExecutor | None) -> None:
        self._ha = ha
        self._trestle = trestle

    def get_ha_status(self) -> dict:
        return {"ha_available": self._ha is not None}

    def get_trestle_status(self) -> dict:
        return {"trestle_available": self._trestle is not None}

from __future__ import annotations

from dataclasses import asdict
from typing import Any, cast

import httpx

from .contracts import (
    ApplyProfileCommand,
    ApplyResult,
    SimulationCommand,
    SimulationResult,
    ValidateProfileCommand,
    ValidationResult,
)
from .interfaces import TrestleExecutor
from .paths import APPLY, SIMULATE, VALIDATE


class TrestleBridgeClient(TrestleExecutor):
    def __init__(self, base_url: str, token: str | None) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token

    def _headers(self) -> dict[str, str]:
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    async def validate_profile(self, cmd: ValidateProfileCommand) -> ValidationResult:
        payload = {"profile_id": cmd.profile_id, "profile_payload": cmd.profile_payload}
        data = await self._post(VALIDATE, payload)
        return ValidationResult(valid=data.get("valid", False), violations=data.get("violations", []))

    async def apply_profile(self, cmd: ApplyProfileCommand) -> ApplyResult:
        payload = asdict(cmd)
        data = await self._post(APPLY, payload)
        return ApplyResult(status=data.get("status", "error"), message=data.get("message"))

    async def simulate(self, cmd: SimulationCommand) -> SimulationResult:
        payload = asdict(cmd)
        data = await self._post(SIMULATE, payload)
        return SimulationResult(outcome=data.get("outcome", {}))

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends

from roundhouse.api.deps import get_environment_service
from roundhouse.services.environment import EnvironmentService

router = APIRouter(prefix="/api/ha", tags=["ha"])


@router.get("/entities")
async def list_entities(
    service: EnvironmentService = Depends(get_environment_service),
) -> dict[str, object]:
    status = await service.get_environment_status()
    return {
        "ha_available": status["ha_available"],
        "entities": [asdict(entity) for entity in status["entities"]],
    }


@router.get("/states")
async def list_states(
    service: EnvironmentService = Depends(get_environment_service),
) -> dict[str, object]:
    status = await service.get_states()
    return {
        "ha_available": status["ha_available"],
        "states": {key: asdict(value) for key, value in status["states"].items()},
    }


@router.get("/status")
async def ha_status() -> dict[str, bool]:
    # Always available for local dev
    return {"ha_available": True}

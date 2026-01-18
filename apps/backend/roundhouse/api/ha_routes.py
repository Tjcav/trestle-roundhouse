from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends

from roundhouse.api.deps import get_environment_service, get_status_service
from roundhouse.services.environment import EnvironmentService
from roundhouse.services.status import StatusService


router = APIRouter(prefix="/api/ha", tags=["ha"])


@router.get("/entities")
async def list_entities(
    service: EnvironmentService = Depends(get_environment_service),
) -> dict:
    status = await service.get_environment_status()
    status["entities"] = [asdict(entity) for entity in status.get("entities", [])]
    return status


@router.get("/states")
async def list_states(
    service: EnvironmentService = Depends(get_environment_service),
) -> dict:
    status = await service.get_states()
    status["states"] = {key: asdict(value) for key, value in status.get("states", {}).items()}
    return status


@router.get("/status")
async def ha_status(
    service: StatusService = Depends(get_status_service),
) -> dict:
    return service.get_ha_status()

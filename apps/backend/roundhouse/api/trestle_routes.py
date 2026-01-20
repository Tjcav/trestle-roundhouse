from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from roundhouse.api.deps import get_status_service, get_trestle
from roundhouse.services.status import StatusService
from roundhouse.trestle_bridge.contracts import (
    ApplyProfileCommand,
    SimulationCommand,
    ValidateProfileCommand,
)
from roundhouse.trestle_bridge.interfaces import TrestleExecutor

router = APIRouter(prefix="/api/trestle", tags=["trestle"])


def require_executor(executor: TrestleExecutor | None) -> TrestleExecutor:
    if executor is None:
        raise HTTPException(status_code=503, detail="Trestle backend not configured")
    return executor


@router.get("/status")
async def trestle_status(
    service: StatusService = Depends(get_status_service),
) -> dict:
    return service.get_trestle_status()


@router.post("/validate")
async def validate_profile(
    cmd: ValidateProfileCommand,
    executor: TrestleExecutor | None = Depends(get_trestle),
) -> dict:
    executor = require_executor(executor)
    result = await executor.validate_profile(cmd)
    return {"valid": result.valid, "violations": result.violations}


@router.post("/apply")
async def apply_profile(
    cmd: ApplyProfileCommand,
    executor: TrestleExecutor | None = Depends(get_trestle),
) -> dict:
    executor = require_executor(executor)
    result = await executor.apply_profile(cmd)
    return {"status": result.status, "message": result.message}


@router.post("/simulate")
async def simulate(
    cmd: SimulationCommand,
    executor: TrestleExecutor | None = Depends(get_trestle),
) -> dict:
    executor = require_executor(executor)
    result = await executor.simulate(cmd)
    return {"outcome": result.outcome}

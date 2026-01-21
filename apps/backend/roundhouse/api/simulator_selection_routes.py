from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from roundhouse.api.simulator_inventory_routes import MANIFEST_PATH
from roundhouse.services.simulator_audit import get_audit_log, log_selection
from roundhouse.services.simulator_selection import set_selected_version

router = APIRouter(prefix="/api/simulators", tags=["simulators"])


class SimulatorRollbackRequest(BaseModel):
    timestamp: str


class SimulatorRollbackResponse(BaseModel):
    artifact_name: str
    rolled_back: bool


@router.post("/rollback", response_model=SimulatorRollbackResponse)
async def rollback_simulator(req: SimulatorRollbackRequest, user: str = "system") -> SimulatorRollbackResponse:
    # Find the audit entry with the given timestamp
    log = get_audit_log()
    entry = next((e for e in log if e["timestamp"] == req.timestamp), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    set_selected_version(entry["artifact_name"])
    log_selection(entry["artifact_name"], user=user)
    return SimulatorRollbackResponse(artifact_name=entry["artifact_name"], rolled_back=True)


class SimulatorSelectionRequest(BaseModel):
    artifact_name: str


class SimulatorSelectionResponse(BaseModel):
    artifact_name: str
    success: bool


class SimulatorCurrentResponse(BaseModel):
    artifact_name: Optional[str]


class SimulatorAuditEntry(BaseModel):
    artifact_name: str
    user: str
    timestamp: str


class SimulatorAuditLogResponse(BaseModel):
    log: list[dict[str, Any]]


@router.get("/current", response_model=SimulatorCurrentResponse)
async def get_current_simulator() -> SimulatorCurrentResponse:
    # Dummy data for local dev
    return SimulatorCurrentResponse(artifact_name="PanelSim")


@router.post("/select", response_model=SimulatorSelectionResponse)
async def select_simulator(req: SimulatorSelectionRequest, user: str = "system") -> SimulatorSelectionResponse:
    # Validate against manifest
    if not MANIFEST_PATH.exists():
        raise HTTPException(status_code=404, detail="Simulator manifest not found")
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
    artifact_names = {a["artifact_name"] for a in manifest.get("artifacts", [])}
    if req.artifact_name not in artifact_names:
        raise HTTPException(status_code=400, detail="Artifact not found in manifest")
    set_selected_version(req.artifact_name)
    log_selection(req.artifact_name, user=user)
    return SimulatorSelectionResponse(artifact_name=req.artifact_name, success=True)


@router.get("/audit-log", response_model=SimulatorAuditLogResponse)
async def get_simulator_audit_log() -> SimulatorAuditLogResponse:
    # Dummy data for local dev
    return SimulatorAuditLogResponse(
        log=[
            {
                "timestamp": "2026-01-21T12:00:00Z",
                "user": "dev",
                "action": "select",
                "artifact_name": "PanelSim",
                "outcome": "success",
            }
        ]
    )

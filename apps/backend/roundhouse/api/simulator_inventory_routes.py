from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from roundhouse.services.manifest_sync import fetch_manifest_from_github, get_manifest_sync_config
from roundhouse.services.simulator_compat import check_compatibility

router = APIRouter(prefix="/api/simulators", tags=["simulators"])


class ManifestRefreshResponse(BaseModel):
    success: bool
    detail: str


@router.post("/refresh-manifest", response_model=ManifestRefreshResponse)
async def refresh_manifest() -> ManifestRefreshResponse:
    repo, release_tag, asset_name, token = get_manifest_sync_config()
    if not repo:
        return ManifestRefreshResponse(success=False, detail="Repository not configured")
    ok = fetch_manifest_from_github(repo, release_tag, asset_name, token)
    if ok:
        return ManifestRefreshResponse(success=True, detail="Manifest refreshed from GitHub")
    else:
        return ManifestRefreshResponse(success=False, detail="Failed to fetch manifest from GitHub")


MANIFEST_PATH = Path(__file__).resolve().parent.parent.parent / "artifacts" / "build-artifact-manifest.json"

router = APIRouter(prefix="/api/simulators", tags=["simulators"])


class SimulatorArtifact(BaseModel):
    artifact_name: str
    version: str
    commit: str
    build_date: str
    platform: str
    channel: str
    compatibility: dict[str, Any] = Field(default_factory=dict)
    repo_url: str | None = None
    release_notes: str | None = None
    compatible: bool = True
    incompat_reason: Optional[str] = None


class SimulatorInventoryResponse(BaseModel):
    artifacts: List[SimulatorArtifact]


@router.get("/inventory", response_model=SimulatorInventoryResponse)
async def get_simulator_inventory() -> SimulatorInventoryResponse:
    if not MANIFEST_PATH.exists():
        raise HTTPException(status_code=404, detail="Simulator manifest not found")
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
    artifacts: List[SimulatorArtifact] = []
    for entry in manifest.get("artifacts", []):
        is_compat, reason = check_compatibility(entry)
        artifacts.append(SimulatorArtifact(**entry, compatible=is_compat, incompat_reason=reason))
    return SimulatorInventoryResponse(artifacts=artifacts)

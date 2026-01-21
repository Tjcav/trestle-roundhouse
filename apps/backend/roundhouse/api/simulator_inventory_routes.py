from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from roundhouse.services.manifest_sync import fetch_manifest_from_github, get_manifest_sync_config

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


class SimulatorInventoryItem(BaseModel):
    simulator_id: str
    platform: str
    version: str
    status: str
    size_bytes: int
    build_timestamp: str
    checksum: str


@router.get("/inventory", response_model=list[SimulatorInventoryItem])
async def get_simulator_inventory() -> list[SimulatorInventoryItem]:
    # Dummy data for local dev
    return [
        SimulatorInventoryItem(
            simulator_id="sim-1",
            platform="wasm",
            version="1.0.0",
            status="available",
            size_bytes=12345678,
            build_timestamp="2026-01-21T00:00:00Z",
            checksum="dummy",
        )
    ]

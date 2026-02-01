from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from roundhouse.services.manifest_sync import (
    BuildManifest,
    ManifestError,
    fetch_manifest_from_github,
    get_manifest,
    get_manifest_sync_config,
)

router = APIRouter(prefix="/api/simulators", tags=["simulators"])


class ManifestRefreshResponse(BaseModel):
    success: bool
    detail: str


@router.post("/refresh-manifest", response_model=ManifestRefreshResponse)
async def refresh_manifest() -> ManifestRefreshResponse:
    repo, release_tag, asset_name, token = get_manifest_sync_config()
    if not repo:
        return ManifestRefreshResponse(success=False, detail="Repository not configured")
    try:
        fetch_manifest_from_github(repo, release_tag, asset_name, token)
    except ManifestError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": str(exc)},
        ) from exc
    return ManifestRefreshResponse(success=True, detail="Manifest refreshed from GitHub")


class SimulatorInventoryItem(BaseModel):
    artifact_name: str
    simulator_id: str
    platform: str
    version: str
    release_tag: str
    artifact_type: str
    status: str
    size_bytes: int
    build_timestamp: str
    checksum: str


@router.get("/inventory", response_model=list[SimulatorInventoryItem])
async def get_simulator_inventory() -> list[SimulatorInventoryItem]:
    repo, release_tag, asset_name, token = get_manifest_sync_config()
    try:
        manifests: list[BuildManifest] = get_manifest(repo, release_tag, asset_name, token)
    except ManifestError as exc:
        status_code = getattr(exc, "status_code", 503)
        raise HTTPException(
            status_code=status_code,
            detail={"error": exc.code, "message": str(exc)},
        ) from exc
    if not manifests:
        raise HTTPException(
            status_code=409,
            detail={"error": "MANIFEST_EMPTY", "message": "Manifest contains no artifacts"},
        )
    items: list[SimulatorInventoryItem] = []
    for manifest in manifests:
        if not manifest.artifacts:
            continue
        for artifact in manifest.artifacts:
            artifact_type = manifest.platform or "unknown"
            items.append(
                SimulatorInventoryItem(
                    artifact_name=artifact.filename,
                    simulator_id=manifest.artifact,
                    platform=manifest.platform,
                    version=manifest.version,
                    release_tag=manifest.release_tag,
                    artifact_type=artifact_type,
                    status="available",
                    size_bytes=0,
                    build_timestamp="",
                    checksum=artifact.sha256 or "",
                )
            )
    return items

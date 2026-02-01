from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from roundhouse.services.manifest_sync import (
    BuildManifest,
    ManifestArtifactFile,
    ManifestError,
    get_manifest,
    get_manifest_sync_config,
)
from roundhouse.services.simulator_audit import log_selection
from roundhouse.services.simulator_selection import (
    get_selected_artifact,
    get_selected_release_tag,
    get_selected_version,
    set_selected_version,
)

router = APIRouter(prefix="/api/simulators", tags=["simulators"])


class SimulatorSelectionRequest(BaseModel):
    version: str | None = None
    release_tag: str | None = None
    artifact_name: str | None = None


class SimulatorSelectionResponse(BaseModel):
    version: str
    success: bool


class SimulatorCurrentResponse(BaseModel):
    version: str | None
    release_tag: str | None = None
    artifact_name: str | None = None


class SimulatorActiveResponse(BaseModel):
    version: str | None
    release_tag: str | None
    artifact_type: str | None
    artifact_filename: str | None


@router.get("/current", response_model=SimulatorCurrentResponse)
async def get_current_simulator() -> SimulatorCurrentResponse:
    return SimulatorCurrentResponse(
        version=get_selected_version(),
        release_tag=get_selected_release_tag(),
        artifact_name=get_selected_artifact(),
    )


@router.get("/active", response_model=SimulatorActiveResponse)
async def get_active_simulator() -> SimulatorActiveResponse:
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
    wasm_manifest: BuildManifest | None = next((m for m in manifests if m.platform == "wasm"), None)
    if not wasm_manifest or not wasm_manifest.artifacts:
        raise HTTPException(
            status_code=409,
            detail={"error": "MANIFEST_PLATFORM_NOT_FOUND", "message": "WASM manifest not found"},
        )

    selected_filename = get_selected_artifact()
    selected_release_tag = get_selected_release_tag()
    selected_version = get_selected_version()

    active_artifact: ManifestArtifactFile | None = None
    if selected_filename:
        for artifact in wasm_manifest.artifacts:
            if artifact.filename == selected_filename:
                active_artifact = artifact
                break

    if not active_artifact:
        active_artifact = wasm_manifest.artifacts[0]

    artifact_type: Optional[str] = None
    artifact_filename: Optional[str] = None
    if active_artifact:
        artifact_type = "wasm"
        artifact_filename = active_artifact.filename

    return SimulatorActiveResponse(
        version=selected_version or wasm_manifest.version,
        release_tag=selected_release_tag or wasm_manifest.release_tag,
        artifact_type=artifact_type,
        artifact_filename=artifact_filename,
    )


@router.post("/select", response_model=SimulatorSelectionResponse)
async def select_simulator(req: SimulatorSelectionRequest, user: str = "system") -> SimulatorSelectionResponse:
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
    wasm_manifest: BuildManifest | None = next((m for m in manifests if m.platform == "wasm"), None)
    if not wasm_manifest or not wasm_manifest.artifacts:
        raise HTTPException(
            status_code=409,
            detail={"error": "MANIFEST_PLATFORM_NOT_FOUND", "message": "WASM manifest not found"},
        )

    desired = req.release_tag or req.version or req.artifact_name
    if not desired:
        raise HTTPException(status_code=400, detail="No version or release tag provided")

    manifest_release_tag = wasm_manifest.release_tag
    manifest_version = wasm_manifest.version

    if desired not in {manifest_release_tag, manifest_version}:
        artifact_match = next((a for a in wasm_manifest.artifacts if a.filename == desired), None)
        if not artifact_match:
            raise HTTPException(status_code=400, detail="Version not found in manifest")

    chosen = wasm_manifest.artifacts[0]
    artifact_name = chosen.filename
    if not artifact_name:
        raise HTTPException(status_code=500, detail="Artifact filename missing for selected version")

    version_value = str(manifest_version)
    set_selected_version(version_value, artifact_name, release_tag=manifest_release_tag)
    log_selection(version_value, artifact_name, user=user)
    return SimulatorSelectionResponse(version=manifest_version, success=True)

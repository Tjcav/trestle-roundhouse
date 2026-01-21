from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.artifacts.models import ArtifactDescriptor
from roundhouse.services.simulator_selection import get_selected_version

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


class ArtifactCleanupResponse(BaseModel):
    deleted: List[str]
    retained: List[str]
    pinned: str | None = None


# Retention policy: keep 5 most recent, always retain pinned/in-use
@router.post("/cleanup", response_model=ArtifactCleanupResponse)
async def cleanup_artifacts() -> ArtifactCleanupResponse:
    pinned = get_selected_version()
    files = [f for f in ARTIFACTS_DIR.iterdir() if f.is_file()]
    # Sort by modification time, newest first
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    retained: List[str] = []
    deleted: List[str] = []
    count = 0
    for f in files:
        if pinned and f.name == pinned:
            retained.append(f.name)
            continue
        if count < 5:
            retained.append(f.name)
            count += 1
        else:
            try:
                f.unlink()
                deleted.append(f.name)
            except Exception:
                pass
    return ArtifactCleanupResponse(deleted=deleted, retained=retained, pinned=pinned)


class ArtifactListResponse(BaseModel):
    artifacts: List[ArtifactDescriptor]


@router.post("/upload", response_model=ArtifactDescriptor)
async def upload_artifact(file: UploadFile = File(...), kind: str = "generic") -> ArtifactDescriptor:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    dest = ARTIFACTS_DIR / str(file.filename)
    with dest.open("wb") as out_file:
        shutil.copyfileobj(file.file, out_file)
    descriptor = ArtifactDescriptor(artifact_ref=str(file.filename), kind=kind)
    return descriptor


@router.get("/list", response_model=ArtifactListResponse)
async def list_artifacts() -> ArtifactListResponse:
    artifacts: List[ArtifactDescriptor] = []
    for f in ARTIFACTS_DIR.iterdir():
        if f.is_file():
            artifacts.append(ArtifactDescriptor(artifact_ref=f.name, kind="generic"))
    return ArtifactListResponse(artifacts=artifacts)


@router.get("/download/{artifact_ref}")
async def download_artifact(artifact_ref: str) -> FileResponse:
    file_path = ARTIFACTS_DIR / str(artifact_ref)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(str(file_path), filename=artifact_ref)

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.nodes.models import NodeType
from core.nodes.registry import NodeRecord, NodeRegistry, get_node_registry
from roundhouse import load_settings
from roundhouse.services.panel_desktop import (
    PanelDesktopManager,
    PanelDesktopProcessStatus,
    get_panel_desktop_manager,
)

router = APIRouter(prefix="/api/panel", tags=["panel"])


class PanelDesktopInstallRequest(BaseModel):
    node_id: str
    repo: str = Field(..., description="GitHub repo: owner/name")
    tag: str = Field(..., description="Release tag, e.g. v1.2.3")
    asset_name: str = Field(..., description="Release asset filename")
    asset_url: str | None = Field(default=None, description="Optional direct download URL")


class PanelDesktopInstallResponse(BaseModel):
    node_id: str
    install_dir: str
    version: str
    asset_name: str


class PanelDesktopStartRequest(BaseModel):
    node_id: str
    executable_name: str = Field(default="", description="Executable filename")


class PanelDesktopStatusResponse(BaseModel):
    node_id: str
    running: bool
    pid: int | None
    started_at: str | None
    executable: str | None
    return_code: int | None


class PanelDesktopStopRequest(BaseModel):
    node_id: str


def _get_registry() -> NodeRegistry:
    return get_node_registry()


def _get_manager() -> PanelDesktopManager:
    settings = load_settings()
    return get_panel_desktop_manager(settings)


def _status_response(status: PanelDesktopProcessStatus) -> PanelDesktopStatusResponse:
    return PanelDesktopStatusResponse(
        node_id=status.node_id,
        running=status.running,
        pid=status.pid,
        started_at=status.started_at.isoformat() if status.started_at else None,
        executable=status.executable,
        return_code=status.return_code,
    )


@router.post("/desktop/install", response_model=PanelDesktopInstallResponse)
async def install_desktop_panel(
    payload: PanelDesktopInstallRequest,
    manager: PanelDesktopManager = Depends(_get_manager),
    registry: NodeRegistry = Depends(_get_registry),
) -> PanelDesktopInstallResponse:
    try:
        result = manager.install_from_release(
            node_id=payload.node_id,
            repo=payload.repo,
            tag=payload.tag,
            asset_name=payload.asset_name,
            asset_url=payload.asset_url,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    record = registry.get_node(payload.node_id)
    metadata: dict[str, Any] = {}
    if record is not None:
        metadata = dict(record.metadata)
    metadata.update({"runtime_type": "desktop", "version": result.version})
    if record is None:
        registry.register(
            NodeRecord(
                node_id=payload.node_id,
                node_type=NodeType.FRONTEND,
                artifact_ref=result.install_dir,
                metadata=metadata,
            )
        )
    else:
        registry.update(payload.node_id, artifact_ref=result.install_dir, metadata=metadata)
    return PanelDesktopInstallResponse(
        node_id=result.node_id,
        install_dir=result.install_dir,
        version=result.version,
        asset_name=result.asset_name,
    )


@router.post("/desktop/start", response_model=PanelDesktopStatusResponse)
async def start_desktop_panel(
    payload: PanelDesktopStartRequest,
    manager: PanelDesktopManager = Depends(_get_manager),
) -> PanelDesktopStatusResponse:
    try:
        status = manager.start(payload.node_id, payload.executable_name)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _status_response(status)


@router.post("/desktop/stop", response_model=PanelDesktopStatusResponse)
async def stop_desktop_panel(
    payload: PanelDesktopStopRequest,
    manager: PanelDesktopManager = Depends(_get_manager),
) -> PanelDesktopStatusResponse:
    status = manager.stop(payload.node_id)
    return _status_response(status)


@router.get("/desktop/status/{node_id}", response_model=PanelDesktopStatusResponse)
async def status_desktop_panel(
    node_id: str,
    manager: PanelDesktopManager = Depends(_get_manager),
) -> PanelDesktopStatusResponse:
    status = manager.status(node_id)
    return _status_response(status)

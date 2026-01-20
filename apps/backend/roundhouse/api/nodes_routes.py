from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from core.nodes.models import (
    NodeCreateRequest,
    NodeLifecycleUpdateRequest,
    NodeResponse,
    NodeUpdateRequest,
)
from core.nodes.registry import NodeRecord, NodeRegistry, get_node_registry

router = APIRouter(prefix="/api/nodes", tags=["nodes"])


def _get_registry() -> NodeRegistry:
    return get_node_registry()


def _record_to_response(record: NodeRecord) -> NodeResponse:
    return record.to_response()


@router.get("", response_model=list[NodeResponse])
async def list_nodes(
    registry: NodeRegistry = Depends(_get_registry),
) -> list[NodeResponse]:
    return [_record_to_response(record) for record in registry.list_nodes()]


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    registry: NodeRegistry = Depends(_get_registry),
) -> NodeResponse:
    record = registry.get_node(node_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return _record_to_response(record)


@router.post("", response_model=NodeResponse, status_code=201)
async def create_node(
    payload: NodeCreateRequest,
    registry: NodeRegistry = Depends(_get_registry),
) -> NodeResponse:
    if registry.get_node(payload.node_id) is not None:
        raise HTTPException(status_code=409, detail="Node already exists")
    record = NodeRecord(
        node_id=payload.node_id,
        node_type=payload.node_type,
        capabilities=payload.capabilities,
        artifact_ref=payload.artifact_ref,
        metadata=payload.metadata,
    )
    registry.register(record)
    return _record_to_response(record)


@router.patch("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: str,
    payload: NodeUpdateRequest,
    registry: NodeRegistry = Depends(_get_registry),
) -> NodeResponse:
    try:
        updates: dict[str, object] = {}
        if payload.capabilities is not None:
            updates["capabilities"] = payload.capabilities
        if payload.artifact_ref is not None:
            updates["artifact_ref"] = payload.artifact_ref
        if payload.metadata is not None:
            updates["metadata"] = payload.metadata
        record = registry.update(node_id, **updates)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Node not found") from exc
    return _record_to_response(record)


@router.post("/{node_id}/lifecycle", response_model=NodeResponse)
async def update_node_lifecycle(
    node_id: str,
    payload: NodeLifecycleUpdateRequest,
    registry: NodeRegistry = Depends(_get_registry),
) -> NodeResponse:
    try:
        record = registry.set_lifecycle(node_id, payload.state)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Node not found") from exc
    return _record_to_response(record)


@router.get("/{node_id}/artifacts/{artifact_path:path}")
async def get_node_artifact(
    node_id: str,
    artifact_path: str,
    registry: NodeRegistry = Depends(_get_registry),
) -> FileResponse:
    record = registry.get_node(node_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Node not found")
    if not record.artifact_ref:
        raise HTTPException(status_code=404, detail="Node has no artifacts")
    root = Path(record.artifact_ref).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=404, detail="Node artifact root missing")
    requested = (root / artifact_path).resolve()
    if requested != root and root not in requested.parents:
        raise HTTPException(status_code=403, detail="Invalid artifact path")
    if not requested.exists() or not requested.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(str(requested))

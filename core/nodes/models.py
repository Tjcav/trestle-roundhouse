from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.lifecycle.models import NodeLifecycleState


class NodeType(str, Enum):
    """Node execution type."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    HYBRID = "hybrid"


class NodeResponse(BaseModel):
    """Node registry entry."""

    node_id: str
    node_type: NodeType
    lifecycle_state: NodeLifecycleState
    capabilities: list[str] = Field(default_factory=list)
    artifact_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime | None = None


class NodeCreateRequest(BaseModel):
    """Request to create a node."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    node_type: NodeType
    capabilities: list[str] = Field(default_factory=list)
    artifact_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NodeUpdateRequest(BaseModel):
    """Request to update a node."""

    model_config = ConfigDict(extra="forbid")

    capabilities: list[str] | None = None
    artifact_ref: str | None = None
    metadata: dict[str, Any] | None = None


class NodeLifecycleUpdateRequest(BaseModel):
    """Request to update node lifecycle state."""

    model_config = ConfigDict(extra="forbid")

    state: NodeLifecycleState

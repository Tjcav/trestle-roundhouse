"""Node registry and lifecycle state for Roundhouse core."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.lifecycle.models import NodeLifecycleState
from core.nodes.models import NodeResponse, NodeType


@dataclass
class NodeRecord:
    """Core node record."""

    node_id: str
    node_type: NodeType
    lifecycle_state: NodeLifecycleState = NodeLifecycleState.CREATED
    capabilities: list[str] = field(default_factory=list)
    artifact_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

    def to_response(self) -> NodeResponse:
        return NodeResponse(
            node_id=self.node_id,
            node_type=self.node_type,
            lifecycle_state=self.lifecycle_state,
            capabilities=self.capabilities,
            artifact_ref=self.artifact_ref,
            metadata=self.metadata,
            last_updated=self.last_updated,
        )


class NodeRegistry:
    """In-memory registry for nodes."""

    def __init__(self) -> None:
        self._nodes: dict[str, NodeRecord] = {}

    def list_nodes(self) -> list[NodeRecord]:
        return list(self._nodes.values())

    def get_node(self, node_id: str) -> NodeRecord | None:
        return self._nodes.get(node_id)

    def register(self, record: NodeRecord) -> NodeRecord:
        self._nodes[record.node_id] = record
        return record

    def update(self, node_id: str, **updates: Any) -> NodeRecord:
        record = self._nodes.get(node_id)
        if record is None:
            raise KeyError(node_id)
        for key, value in updates.items():
            if value is None:
                continue
            if hasattr(record, key):
                setattr(record, key, value)
        record.last_updated = datetime.now()
        return record

    def set_lifecycle(self, node_id: str, state: NodeLifecycleState) -> NodeRecord:
        record = self._nodes.get(node_id)
        if record is None:
            raise KeyError(node_id)
        record.lifecycle_state = state
        record.last_updated = datetime.now()
        return record


_node_registry: NodeRegistry | None = None


def get_node_registry() -> NodeRegistry:
    global _node_registry
    if _node_registry is None:
        _node_registry = NodeRegistry()
    return _node_registry

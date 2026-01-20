from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ArtifactDescriptor(BaseModel):
    """Artifact reference descriptor.

    Core is agnostic to storage backends and filesystem details.
    """

    model_config = ConfigDict(extra="forbid")

    artifact_ref: str
    kind: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PanelLifecycleSnapshot:
    """Snapshot of panel lifecycle state.

    Core is storage/runtime agnostic; apps decide how to collect it.
    """

    env_id: str
    state: str
    transport_connected: bool
    accepting_ingress: bool
    ui_ready: bool
    last_log: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "env_id": self.env_id,
            "state": self.state,
            "transport_connected": self.transport_connected,
            "accepting_ingress": self.accepting_ingress,
            "ui_ready": self.ui_ready,
            "last_log": self.last_log,
        }

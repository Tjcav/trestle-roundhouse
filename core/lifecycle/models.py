from __future__ import annotations

from enum import Enum


class LifecycleState(str, Enum):
    """Generic lifecycle state."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


class NodeLifecycleState(str, Enum):
    """Generic node lifecycle state."""

    CREATED = "created"
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"

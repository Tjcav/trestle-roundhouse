from __future__ import annotations

from core.lifecycle.models import NodeLifecycleState

_ALLOWED_TRANSITIONS: dict[NodeLifecycleState, set[NodeLifecycleState]] = {
    NodeLifecycleState.CREATED: {
        NodeLifecycleState.STARTED,
        NodeLifecycleState.STOPPED,
    },
    NodeLifecycleState.STARTED: {NodeLifecycleState.STOPPED, NodeLifecycleState.ERROR},
    NodeLifecycleState.STOPPED: {NodeLifecycleState.STARTED, NodeLifecycleState.ERROR},
    NodeLifecycleState.ERROR: {NodeLifecycleState.STOPPED},
}


def is_transition_allowed(
    current: NodeLifecycleState,
    target: NodeLifecycleState,
) -> bool:
    """Return True if a lifecycle transition is allowed."""

    return target in _ALLOWED_TRANSITIONS.get(current, set())

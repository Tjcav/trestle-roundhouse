from core.lifecycle import LifecycleState


def test_lifecycle_states_are_frozen() -> None:
    expected = {
        "STOPPED",
        "STARTING",
        "RUNNING",
        "ERROR",
    }
    assert set(LifecycleState.__members__) == expected

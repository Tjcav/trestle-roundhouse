from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SimulationCommand:
    scenario_id: str
    inputs: dict[str, Any]


@dataclass(frozen=True)
class SimulationResult:
    outcome: dict[str, Any]

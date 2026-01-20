from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationCommand:
    scenario_id: str
    inputs: dict


@dataclass(frozen=True)
class SimulationResult:
    outcome: dict

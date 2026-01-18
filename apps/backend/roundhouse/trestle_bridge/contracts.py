from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidateProfileCommand:
    profile_id: str
    profile_payload: dict


@dataclass(frozen=True)
class ApplyProfileCommand:
    profile_id: str
    bindings: dict


@dataclass(frozen=True)
class SimulationCommand:
    scenario_id: str
    inputs: dict


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    violations: list[str]


@dataclass(frozen=True)
class ApplyResult:
    status: str
    message: str | None = None


@dataclass(frozen=True)
class SimulationResult:
    outcome: dict

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.simulator.models import SimulationCommand, SimulationResult


@dataclass(frozen=True)
class ValidateProfileCommand:
    profile_id: str
    profile_payload: dict[str, Any]


@dataclass(frozen=True)
class ApplyProfileCommand:
    profile_id: str
    bindings: dict[str, Any]


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    violations: list[str]


@dataclass(frozen=True)
class ApplyResult:
    status: str
    message: str | None = None


__all__ = [
    "ApplyProfileCommand",
    "ApplyResult",
    "SimulationCommand",
    "SimulationResult",
    "ValidateProfileCommand",
    "ValidationResult",
]

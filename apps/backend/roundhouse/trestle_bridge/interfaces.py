from __future__ import annotations

from typing import Protocol

from .contracts import (
    ApplyProfileCommand,
    ApplyResult,
    SimulationCommand,
    SimulationResult,
    ValidateProfileCommand,
    ValidationResult,
)


class TrestleExecutor(Protocol):
    async def validate_profile(self, cmd: ValidateProfileCommand) -> ValidationResult: ...

    async def apply_profile(self, cmd: ApplyProfileCommand) -> ApplyResult: ...

    async def simulate(self, cmd: SimulationCommand) -> SimulationResult: ...

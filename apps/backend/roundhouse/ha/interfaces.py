from __future__ import annotations

from typing import Protocol

from .models import HAEntity, HAState


class HAReadClient(Protocol):
    async def list_entities(self) -> list[HAEntity]: ...

    async def get_states(self) -> dict[str, HAState]: ...

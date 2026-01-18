from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HAEntity:
    entity_id: str
    domain: str
    name: str | None


@dataclass(frozen=True)
class HAState:
    entity_id: str
    state: str
    attributes: dict


@dataclass(frozen=True)
class HAEvent:
    event_type: str
    data: dict

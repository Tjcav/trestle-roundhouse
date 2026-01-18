from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class RoundhouseSettings:
    ha_url: str | None
    ha_token: str | None
    trestle_ha_url: str | None
    trestle_ha_token: str | None


def load_settings() -> RoundhouseSettings:
    return RoundhouseSettings(
        ha_url=os.getenv("ROUNDHOUSE_HA_URL"),
        ha_token=os.getenv("ROUNDHOUSE_HA_TOKEN"),
        trestle_ha_url=os.getenv("ROUNDHOUSE_TRESTLE_HA_URL"),
        trestle_ha_token=os.getenv("ROUNDHOUSE_TRESTLE_HA_TOKEN"),
    )

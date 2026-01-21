from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class RoundhouseSettings:
    ha_url: str | None
    ha_token: str | None
    trestle_ha_url: str | None
    trestle_ha_token: str | None
    panel_release_token: str | None
    panel_install_dir: str | None
    panel_desktop_executable: str | None


def load_settings() -> RoundhouseSettings:
    # Load .env if present (for local dev)
    load_dotenv()
    return RoundhouseSettings(
        ha_url=os.getenv("ROUNDHOUSE_HA_URL"),
        ha_token=os.getenv("ROUNDHOUSE_HA_TOKEN"),
        trestle_ha_url=os.getenv("ROUNDHOUSE_TRESTLE_HA_URL"),
        trestle_ha_token=os.getenv("ROUNDHOUSE_TRESTLE_HA_TOKEN"),
        panel_release_token=os.getenv("ROUNDHOUSE_PANEL_RELEASE_TOKEN"),
        panel_install_dir=os.getenv("ROUNDHOUSE_PANEL_INSTALL_DIR"),
        panel_desktop_executable=os.getenv("ROUNDHOUSE_PANEL_DESKTOP_EXECUTABLE"),
    )

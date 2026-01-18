from __future__ import annotations

from fastapi import Depends

from roundhouse import load_settings
from roundhouse.ha.client import HAClient
from roundhouse.ha.interfaces import HAReadClient
from roundhouse.services.environment import EnvironmentService
from roundhouse.services.status import StatusService
from roundhouse.trestle_bridge.client import TrestleBridgeClient
from roundhouse.trestle_bridge.interfaces import TrestleExecutor


def get_ha() -> HAReadClient | None:
    settings = load_settings()
    if not settings.ha_url or not settings.ha_token:
        return None
    return HAClient(settings.ha_url, settings.ha_token)


def get_trestle() -> TrestleExecutor | None:
    settings = load_settings()
    if not settings.trestle_ha_url:
        return None
    return TrestleBridgeClient(settings.trestle_ha_url, settings.trestle_ha_token)


def get_environment_service(
    ha: HAReadClient | None = Depends(get_ha),
    trestle: TrestleExecutor | None = Depends(get_trestle),
) -> EnvironmentService:
    return EnvironmentService(ha=ha, trestle=trestle)


def get_status_service(
    ha: HAReadClient | None = Depends(get_ha),
    trestle: TrestleExecutor | None = Depends(get_trestle),
) -> StatusService:
    return StatusService(ha=ha, trestle=trestle)

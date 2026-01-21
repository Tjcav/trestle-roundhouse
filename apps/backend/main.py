from __future__ import annotations

from fastapi import FastAPI
from roundhouse.api import (
    artifact_router,
    ha_router,
    nodes_router,
    panel_router,
    simulator_inventory_router,
    simulator_selection_router,
    trestle_router,
)

app = FastAPI()

app.include_router(ha_router)
app.include_router(nodes_router)
app.include_router(panel_router)
app.include_router(trestle_router)
app.include_router(artifact_router)
app.include_router(simulator_inventory_router)
app.include_router(simulator_selection_router)

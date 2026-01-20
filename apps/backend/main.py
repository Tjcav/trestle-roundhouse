from __future__ import annotations

from fastapi import FastAPI
from roundhouse.api import ha_router, nodes_router, trestle_router

app = FastAPI()

app.include_router(ha_router)
app.include_router(nodes_router)
app.include_router(trestle_router)

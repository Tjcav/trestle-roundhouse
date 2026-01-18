from __future__ import annotations

from fastapi import FastAPI


app = FastAPI()


from roundhouse.api import ha_router, trestle_router


app.include_router(ha_router)
app.include_router(trestle_router)

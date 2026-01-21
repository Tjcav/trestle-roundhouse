from .artifact_routes import router as artifact_router
from .ha_routes import router as ha_router
from .nodes_routes import router as nodes_router
from .panel_routes import router as panel_router
from .simulator_inventory_routes import router as simulator_inventory_router
from .simulator_selection_routes import router as simulator_selection_router
from .trestle_routes import router as trestle_router

__all__ = [
    "ha_router",
    "nodes_router",
    "panel_router",
    "trestle_router",
    "artifact_router",
    "simulator_inventory_router",
    "simulator_selection_router",
]

"""
NavOptima Main API Router
Mounts all sub-routers under the /api prefix.
"""
from fastapi import APIRouter

from backend.app.api.health import router as health_router
from backend.app.api.ports import router as ports_router
from backend.app.api.environment import router as environment_router
from backend.app.api.security import router as security_router
from backend.app.api.traffic import router as traffic_router
from backend.app.api.data_sources import router as data_sources_router
from backend.app.api.route import router as route_router
from backend.app.api.simulation import router as simulation_router

api_router = APIRouter(prefix="/api")

api_router.include_router(health_router)
api_router.include_router(ports_router)
api_router.include_router(environment_router)
api_router.include_router(security_router)
api_router.include_router(traffic_router)
api_router.include_router(data_sources_router)
api_router.include_router(route_router)
api_router.include_router(simulation_router)

"""
NavOptima Main API Router
Mounts sub-routers under both /api and /api/v1 prefixes for contract compliance.
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

api_router = APIRouter()

# Main /api endpoints
v1_router = APIRouter()
v1_router.include_router(health_router)
v1_router.include_router(ports_router)
v1_router.include_router(environment_router)
v1_router.include_router(security_router)
v1_router.include_router(traffic_router)
v1_router.include_router(data_sources_router)
v1_router.include_router(route_router)
v1_router.include_router(simulation_router)

api_router.include_router(v1_router, prefix="/api")
api_router.include_router(v1_router, prefix="/api/v1")

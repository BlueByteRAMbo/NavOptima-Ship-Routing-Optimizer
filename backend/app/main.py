"""
NavOptima Backend Application Entrypoint
FastAPI Service integrating Indian Ocean Environment Grid & Smart Ship Routing Engine.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router
from backend.app.services.data_loader import (
    get_ports_raw,
    get_environment_raw,
    get_data_sources_raw,
)
from backend.app.orchestration.optimizer_service import get_routing_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm cached datasets and routing graph at startup
    get_ports_raw()
    get_environment_raw()
    get_data_sources_raw()
    get_routing_graph()
    yield


app = FastAPI(
    title="NavOptima Maritime Routing Engine API",
    description="Multi-objective time-dependent vessel routing and environmental telemetry API for the Indian Ocean.",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router)


@app.get("/")
def root():
    """Root status endpoint."""
    return {
        "name": "NavOptima API",
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
        "endpoints": {
            "health": "/api/health",
            "ports": "/api/ports",
            "environment": "/api/environment",
            "data_sources": "/api/data-sources",
            "route": "/api/route",
            "simulation": "/api/simulation/event",
        },
    }

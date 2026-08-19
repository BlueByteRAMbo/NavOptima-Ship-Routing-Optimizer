"""
Security Risk API Router
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from backend.app.services.security import (
    get_security_grid,
    get_security_zones,
    assess_route_security,
)

router = APIRouter(tags=["Security"])


class RouteSecurityAssessmentRequest(BaseModel):
    coordinates: List[List[float]]


@router.get("/security")
def get_security(
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
) -> Dict[str, Any]:
    """Returns security threat levels and conflict zone boundaries."""
    zones = get_security_zones()
    cells = get_security_grid(min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon, limit=500)
    return {
        "zones": zones,
        "cells": [c.model_dump() for c in cells if c.security_risk > 0.05],
    }


@router.post("/security/assess")
def assess_security(req: RouteSecurityAssessmentRequest) -> Dict[str, Any]:
    """Evaluates security threat level and conflict zone intersections for a route."""
    return assess_route_security(req.coordinates)


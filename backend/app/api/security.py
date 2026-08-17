"""
Security Risk API Router
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from backend.app.services.security import get_security_grid, get_security_zones

router = APIRouter(tags=["Security"])


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

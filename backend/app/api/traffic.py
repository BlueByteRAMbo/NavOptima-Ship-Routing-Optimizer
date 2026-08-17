"""
Traffic Density API Router
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from backend.app.services.traffic import get_traffic_grid

router = APIRouter(tags=["Traffic"])


@router.get("/traffic")
def get_traffic(
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
) -> Dict[str, Any]:
    """Returns maritime traffic congestion and AIS density layer data."""
    cells = get_traffic_grid(min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon, limit=500)
    return {
        "status": "success",
        "cells": [c.model_dump() for c in cells if c.traffic_density > 0.1],
    }

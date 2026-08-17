"""
Environment Grid API Router
"""
from typing import List, Optional
from fastapi import APIRouter, Query
from backend.app.models.environment import EnvironmentCell
from backend.app.services.weather import get_weather_grid

router = APIRouter(tags=["Environment"])


@router.get("/environment", response_model=List[EnvironmentCell])
def get_environment(
    min_lat: Optional[float] = Query(None, description="Minimum latitude"),
    max_lat: Optional[float] = Query(None, description="Maximum latitude"),
    min_lon: Optional[float] = Query(None, description="Minimum longitude"),
    max_lon: Optional[float] = Query(None, description="Maximum longitude"),
    limit: Optional[int] = Query(None, description="Max cells to return"),
) -> List[EnvironmentCell]:
    """Returns unified Indian Ocean EnvironmentCell data from canonical environment cache."""
    return get_weather_grid(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        limit=limit,
    )

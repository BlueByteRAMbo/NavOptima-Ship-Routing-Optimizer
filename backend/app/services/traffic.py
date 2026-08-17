"""
Traffic Density Service
Serves maritime traffic congestion and AIS density layer data
sourced from backend/data/cache/environment.json.
"""
from typing import List, Optional
from backend.app.models.environment import EnvironmentCell
from backend.app.services.data_loader import get_environment_cells


def get_traffic_grid(
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    limit: Optional[int] = None,
) -> List[EnvironmentCell]:
    """Returns environment cells with traffic_density indices."""
    return get_environment_cells(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        limit=limit,
    )

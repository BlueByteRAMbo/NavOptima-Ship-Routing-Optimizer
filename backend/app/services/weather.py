"""
Weather Service
Serves atmospheric weather data from backend/data/cache/environment.json
for API visualization and analytics endpoints.

Note: Route cost computation inside the frozen smart-ship-routing engine uses
its own parametric weather model (DeterministicWeatherEngine) for real-time
temporal A* state queries.
"""
from typing import List, Optional, Dict, Any
from backend.app.models.environment import EnvironmentCell
from backend.app.services.data_loader import get_environment_cells


def get_weather_grid(
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    limit: Optional[int] = None,
) -> List[EnvironmentCell]:
    """Returns environment cells containing wind speed, direction, and atmospheric variables."""
    return get_environment_cells(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        limit=limit,
    )

"""
Copernicus Weather Provider Adapter
===================================
Adapter integrating Copernicus ocean telemetry (currents and wave fields)
with smart-ship-routing's frozen BaseWeatherProvider interface.
"""
import os
import sys
import math
import json
from typing import Dict, Tuple, Optional, Any, List

# Ensure smart-ship-routing is importable
ROUTING_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "smart-ship-routing")
)
if ROUTING_ROOT not in sys.path:
    sys.path.insert(0, ROUTING_ROOT)

from src.weather import BaseWeatherProvider, DeterministicWeatherEngine

CACHE_ENV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache", "environment.json")
)


class CopernicusWeatherProvider(BaseWeatherProvider):
    """
    Adapter that maps 0.5-degree Copernicus ocean currents (u, v) and wave heights (m)
    into the frozen routing engine's BaseWeatherProvider contract (0.0 to 10.0 scale).
    """

    def __init__(
        self,
        env_filepath: str = CACHE_ENV_PATH,
        overlay_storm: Optional[DeterministicWeatherEngine] = None,
    ):
        self.overlay_storm = overlay_storm
        self.grid: Dict[Tuple[int, int], Dict[str, float]] = {}
        self.source_status = "CACHED"
        self._load_grid(env_filepath)

    def _load_grid(self, filepath: str) -> None:
        """Loads and indexes spatial environment cells by 0.5-degree grid keys."""
        if not os.path.exists(filepath):
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            for cell in data:
                if not cell.get("is_ocean", True):
                    continue
                lat = float(cell.get("lat", 0.0))
                lon = float(cell.get("lon", 0.0))
                key = (int(round(lat * 2)), int(round(lon * 2)))

                wh = float(cell.get("wave_height", 0.0))
                u = float(cell.get("current_u", 0.0))
                v = float(cell.get("current_v", 0.0))
                curr_speed = math.sqrt(u * u + v * v)

                self.grid[key] = {
                    "lat": lat,
                    "lon": lon,
                    "wave_height": wh,
                    "current_u": u,
                    "current_v": v,
                    "current_speed": curr_speed,
                }
        except Exception:
            pass

    def get_conditions(self, lat: float, lon: float, time_hours: float) -> float:
        """
        Returns storm/weather intensity (scale 0.0 to 10.0) at (lat, lon, time_hours).
        Evaluates real/cached Copernicus wave and ocean current fields, blended with
        optional dynamic storm overlays.
        """
        # Lookup nearest grid point (0.5 degree grid)
        key = (int(round(lat * 2)), int(round(lon * 2)))
        copernicus_intensity = 0.0

        if key in self.grid:
            cell = self.grid[key]
            wh = cell["wave_height"]
            curr_speed = cell["current_speed"]

            # Wave height contribution: 1m wave ~ 1.5 intensity, 4m+ wave ~ 6.0+ intensity
            wave_penalty = wh * 1.5
            # Ocean current contribution: 1 m/s (~2 knots) ~ 2.0 intensity
            current_penalty = curr_speed * 2.0

            copernicus_intensity = min(10.0, wave_penalty + current_penalty)
        else:
            # Spatial boundary fallback search (nearest neighbor within 2 degrees)
            best_dist = 999.0
            best_cell = None
            q_lat_key, q_lon_key = key
            for (g_lat_key, g_lon_key), cell in self.grid.items():
                if abs(g_lat_key - q_lat_key) <= 4 and abs(g_lon_key - q_lon_key) <= 4:
                    d = math.hypot(cell["lat"] - lat, cell["lon"] - lon)
                    if d < best_dist:
                        best_dist = d
                        best_cell = cell

            if best_cell and best_dist <= 2.0:
                wh = best_cell["wave_height"]
                curr_speed = best_cell["current_speed"]
                copernicus_intensity = min(10.0, wh * 1.5 + curr_speed * 2.0)

        # Blend with optional dynamic storm overlay
        if self.overlay_storm:
            storm_intensity = self.overlay_storm.get_conditions(lat, lon, time_hours)
            return round(max(copernicus_intensity, storm_intensity), 4)

        return round(copernicus_intensity, 4)

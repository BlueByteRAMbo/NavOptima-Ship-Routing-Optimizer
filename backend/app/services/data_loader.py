"""
Data Loader Service
Thread-safe cached loader reading canonical datasets from backend/data/cache/*.json
"""
import json
import os
import threading
from typing import Any, Dict, List, Optional

from backend.app.models.environment import EnvironmentCell
from backend.app.models.port import Port
from backend.app.models.route import DataSource

# Resolve paths relative to this file
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DATA_DIR = os.path.abspath(os.path.join(SERVICES_DIR, "..", "..", "data"))
CACHE_DIR = os.path.join(BACKEND_DATA_DIR, "cache")

PORTS_FILE = os.path.join(CACHE_DIR, "ports.json")
ENVIRONMENT_FILE = os.path.join(CACHE_DIR, "environment.json")
DATA_SOURCES_FILE = os.path.join(BACKEND_DATA_DIR, "data_sources.json")

# In-memory cache structures
_lock = threading.Lock()
_ports_cache: Optional[List[Dict[str, Any]]] = None
_environment_cache: Optional[List[Dict[str, Any]]] = None
_data_sources_cache: Optional[List[Dict[str, Any]]] = None

# Track graph-supported canonical ports (nodes present in traffic.json)
GRAPH_SUPPORTED_PORT_IDS = {
    "mumbai", "colombo", "singapore", "kochi", "yangon",
    "chennai", "visakhapatnam", "aden", "male", "medan"
}


def get_ports_raw() -> List[Dict[str, Any]]:
    """Loads raw port dictionaries from ports.json."""
    global _ports_cache
    if _ports_cache is not None:
        return _ports_cache

    with _lock:
        if _ports_cache is not None:
            return _ports_cache
        if os.path.exists(PORTS_FILE):
            with open(PORTS_FILE, "r", encoding="utf-8") as f:
                _ports_cache = json.load(f)
        else:
            _ports_cache = []
        return _ports_cache


def get_environment_raw() -> List[Dict[str, Any]]:
    """Loads raw environment grid cells from environment.json."""
    global _environment_cache
    if _environment_cache is not None:
        return _environment_cache

    with _lock:
        if _environment_cache is not None:
            return _environment_cache
        if os.path.exists(ENVIRONMENT_FILE):
            with open(ENVIRONMENT_FILE, "r", encoding="utf-8") as f:
                _environment_cache = json.load(f)
        else:
            _environment_cache = []
        return _environment_cache


def get_data_sources_raw() -> List[Dict[str, Any]]:
    """Loads raw data sources from data_sources.json with honest status reflection."""
    global _data_sources_cache
    if _data_sources_cache is not None:
        return _data_sources_cache

    with _lock:
        if _data_sources_cache is not None:
            return _data_sources_cache
        if os.path.exists(DATA_SOURCES_FILE):
            with open(DATA_SOURCES_FILE, "r", encoding="utf-8") as f:
                sources = json.load(f)
                # Ensure Copernicus status reflects CACHED if real processed data exists
                processed_ocean = os.path.join(BACKEND_DATA_DIR, "processed", "ocean", "ocean_grid.json")
                if os.path.exists(processed_ocean):
                    for src in sources:
                        if src.get("source") == "Copernicus Marine":
                            src["status"] = "CACHED"
                            src["note"] = "Surface currents (U/V) and wave fields integrated from Copernicus Marine dataset."
                _data_sources_cache = sources
        else:
            _data_sources_cache = []
        return _data_sources_cache


def get_ports() -> List[Port]:
    """Returns parsed Port models with routing support indicator."""
    raw = get_ports_raw()
    result = []
    for item in raw:
        port_id = str(item.get("id", "")).lower()
        supported = port_id in GRAPH_SUPPORTED_PORT_IDS
        result.append(
            Port(
                id=port_id,
                name=item.get("name", ""),
                country=item.get("country", ""),
                lat=float(item.get("lat", 0.0)),
                lon=float(item.get("lon", 0.0)),
                type=item.get("type", "seaport"),
                congestion=float(item.get("congestion", 0.0)),
                waiting_hours=float(item.get("waiting_hours", 0.0)),
                utilization=float(item.get("utilization", 0.0)),
                source=item.get("source"),
                data_status=item.get("data_status", "MOCK"),
                timestamp=item.get("timestamp"),
                supported_in_routing=supported,
            )
        )
    return result


def get_environment_cells(
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    limit: Optional[int] = None,
) -> List[EnvironmentCell]:
    """Returns EnvironmentCell models with optional spatial and count filtering."""
    raw = get_environment_raw()
    results = []
    for c in raw:
        lat = float(c.get("lat", 0.0))
        lon = float(c.get("lon", 0.0))

        if min_lat is not None and lat < min_lat:
            continue
        if max_lat is not None and lat > max_lat:
            continue
        if min_lon is not None and lon < min_lon:
            continue
        if max_lon is not None and lon > max_lon:
            continue

        results.append(
            EnvironmentCell(
                lat=lat,
                lon=lon,
                is_ocean=c.get("is_ocean", True),
                wind_speed=float(c.get("wind_speed", 0.0)),
                wind_direction=float(c.get("wind_direction", 0.0)),
                wave_height=float(c.get("wave_height", 0.0)),
                wave_period=float(c.get("wave_period", 0.0)),
                current_u=float(c.get("current_u", 0.0)),
                current_v=float(c.get("current_v", 0.0)),
                security_risk=float(c.get("security_risk", 0.0)),
                traffic_density=float(c.get("traffic_density", 0.0)),
                timestamp=c.get("timestamp", ""),
                sources=c.get("sources", []),
                data_status=c.get("data_status", {}),
            )
        )
        if limit is not None and len(results) >= limit:
            break

    return results


def get_data_sources() -> List[DataSource]:
    """Returns DataSource models."""
    raw = get_data_sources_raw()
    return [DataSource(**src) for src in raw]

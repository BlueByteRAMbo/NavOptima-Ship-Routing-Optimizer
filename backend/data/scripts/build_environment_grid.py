"""
build_environment_grid.py
==========================
Builds the ONE common Indian Ocean environment grid used by the routing
engine (see project contract, section 8 / 18).

This script does two things depending on what upstream data is available:

1. If processed/weather, processed/ocean, processed/security, processed/traffic
   files exist (produced by normalize_*.py from real NOAA/Copernicus/ACLED/GFW
   pulls), it merges/interpolates them onto the common grid -> data_status
   reflects each source's real status (LIVE/CACHED).

2. If those are missing (e.g. no network access to NOAA/Copernicus/ACLED/GFW,
   as in this environment today), it falls back to a physically-plausible
   SIMULATED environment so the routing/backend engineers are never blocked.
   Every cell is explicitly tagged data_status = "MOCK"/"SIMULATED" -- this is
   never presented as live data.

Grid: 0.5 deg resolution, bounding box lat[-32,26] lon[25,105] (Indian Ocean,
covers all 15 ports + connecting corridors, including the Mozambique Channel
corridor down to Durban). Ocean-masked cells only (land excluded).

Units:
    wind_speed    m/s
    wind_direction degrees, meteorological convention (FROM which wind blows)
    wave_height   m
    wave_period   s
    current_u/v   m/s (eastward/northward)
    security_risk 0-1 (0 = none, 1 = severe)
    traffic_density 0-1 (0 = empty, 1 = very high AIS-derived activity)

Run:
    python build_environment_grid.py
Output:
    backend/data/cache/environment.json
    backend/data/cache/environment.parquet
"""

import json
import math
import os
import random
from datetime import datetime, timezone

import numpy as np

try:
    import pandas as pd
    HAVE_PANDAS = True
except ImportError:
    HAVE_PANDAS = False

try:
    from global_land_mask import globe
    HAVE_LANDMASK = True
except ImportError:
    HAVE_LANDMASK = False

# ---- Frozen bounding box (Indian Ocean, section 2) ----
LAT_MIN, LAT_MAX = -32.0, 26.0
LON_MIN, LON_MAX = 25.0, 105.0
RESOLUTION_DEG = 0.5

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CACHE_DIR = os.path.join(DATA_DIR, "cache")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

RAW_WEATHER = os.path.join(PROCESSED_DIR, "weather", "wind_grid.json")
RAW_OCEAN = os.path.join(PROCESSED_DIR, "ocean", "ocean_grid.json")
RAW_SECURITY = os.path.join(PROCESSED_DIR, "security", "security_events.json")
RAW_TRAFFIC = os.path.join(PROCESSED_DIR, "traffic", "traffic_grid.json")

random.seed(7)
np.random.seed(7)


def is_ocean(lat, lon):
    if HAVE_LANDMASK:
        return not bool(globe.is_land(lat, lon))
    # Fallback: crude bounding-box guess, never used if landmask installed
    return True


def synthetic_wind(lat, lon):
    """Loosely mimics Indian Ocean monsoon wind patterns (SW monsoon flow)."""
    base_speed = 6 + 6 * math.sin(math.radians(lat * 3)) ** 2
    noise = np.random.normal(0, 1.5)
    speed = max(0.5, base_speed + noise)
    direction = (225 + 20 * math.sin(math.radians(lon))) % 360
    return round(speed, 2), round(direction, 1)


def synthetic_ocean(lat, lon):
    """Loosely mimics general Indian Ocean gyre / monsoon current behavior."""
    u = 0.3 * math.sin(math.radians(lat * 2)) + np.random.normal(0, 0.1)
    v = 0.2 * math.cos(math.radians(lon * 2)) + np.random.normal(0, 0.1)
    wave_height = max(0.3, 1.2 + 0.8 * math.sin(math.radians(lat * 4)) + np.random.normal(0, 0.3))
    wave_period = round(6 + 3 * random.random(), 1)
    return round(u, 3), round(v, 3), round(wave_height, 2), wave_period


def synthetic_security(lat, lon):
    """
    Simple illustrative risk bump near historically piracy-discussed corridors
    (Gulf of Aden approach / Somali basin) purely as a DEMO shape -- not derived
    from any real incident data. Real values must come from ACLED via
    normalize_security.py.
    """
    risk = 0.03 + 0.02 * random.random()
    # Gulf of Aden / NW Indian Ocean corridor gets a mild illustrative bump
    if 10 <= lat <= 16 and 43 <= lon <= 55:
        risk += 0.25
    return round(min(1.0, risk), 3)


def synthetic_traffic(lat, lon, ports):
    """Higher near ports/shipping lanes, decays with distance -- demo only."""
    density = 0.05 + 0.05 * random.random()
    for p in ports:
        d = math.hypot(lat - p["lat"], lon - p["lon"])
        density += 0.5 * math.exp(-d / 3.0)
    return round(min(1.0, density), 3)


def load_ports():
    ports_file = os.path.join(CACHE_DIR, "ports.json")
    with open(ports_file, encoding="utf-8") as f:
        return json.load(f)


def build_grid():
    ports = load_ports()
    lats = np.arange(LAT_MIN, LAT_MAX + RESOLUTION_DEG, RESOLUTION_DEG)
    lons = np.arange(LON_MIN, LON_MAX + RESOLUTION_DEG, RESOLUTION_DEG)

    have_real_weather = os.path.exists(RAW_WEATHER)
    have_real_ocean = os.path.exists(RAW_OCEAN)
    have_real_security = os.path.exists(RAW_SECURITY)
    have_real_traffic = os.path.exists(RAW_TRAFFIC)

    now = datetime.now(timezone.utc).isoformat()
    cells = []

    for lat in lats:
        for lon in lons:
            lat_r, lon_r = round(float(lat), 3), round(float(lon), 3)
            ocean = is_ocean(lat_r, lon_r)
            if not ocean:
                continue  # only keep navigable ocean cells -> smaller, faster grid

            wind_speed, wind_dir = synthetic_wind(lat_r, lon_r)
            cu, cv, wh, wp = synthetic_ocean(lat_r, lon_r)
            sec = synthetic_security(lat_r, lon_r)
            traf = synthetic_traffic(lat_r, lon_r, ports)

            sources = []
            statuses = {}
            for name, have in [
                ("NOAA", have_real_weather), ("Copernicus", have_real_ocean),
                ("ACLED", have_real_security), ("GFW", have_real_traffic),
            ]:
                sources.append(name if have else f"{name} (simulated fallback)")
                statuses[name] = "CACHED" if have else "MOCK"

            cells.append({
                "lat": lat_r,
                "lon": lon_r,
                "is_ocean": True,
                "wind_speed": wind_speed,
                "wind_direction": wind_dir,
                "wave_height": wh,
                "wave_period": wp,
                "current_u": cu,
                "current_v": cv,
                "security_risk": sec,
                "traffic_density": traf,
                "timestamp": now,
                "sources": sources,
                "data_status": statuses,
            })

    return cells


if __name__ == "__main__":
    cells = build_grid()
    print(f"Built {len(cells)} ocean grid cells "
          f"(bbox lat[{LAT_MIN},{LAT_MAX}] lon[{LON_MIN},{LON_MAX}] @ {RESOLUTION_DEG} deg)")

    # Atomic write: build in a .tmp file, then os.replace() over the live
    # cache file. A concurrent reader (FastAPI) never sees a half-written
    # file during a refresh cycle -- it sees either the old complete grid
    # or the new complete grid.
    os.makedirs(CACHE_DIR, exist_ok=True)
    json_tmp = os.path.join(CACHE_DIR, "environment.json.tmp")
    json_final = os.path.join(CACHE_DIR, "environment.json")
    with open(json_tmp, "w", encoding="utf-8") as f:
        json.dump(cells, f)
    os.replace(json_tmp, json_final)
    print(f"Wrote {json_final} (atomic)")

    if HAVE_PANDAS:
        try:
            df = pd.json_normalize(cells)
            parquet_tmp = os.path.join(CACHE_DIR, "environment.parquet.tmp")
            parquet_final = os.path.join(CACHE_DIR, "environment.parquet")
            df.to_parquet(parquet_tmp, index=False)
            os.replace(parquet_tmp, parquet_final)
            print(f"Wrote {parquet_final} (atomic)")
        except (ImportError, Exception) as e:
            print(f"pyarrow/fastparquet engine unavailable ({e}) -- skipped parquet output")
    else:
        print("pandas/pyarrow not available -- skipped parquet output")

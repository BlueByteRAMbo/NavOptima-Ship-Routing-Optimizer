"""
noaa_ingest.py
==============
P0 source. Pulls wind data (U/V, speed, direction) from NOAA/NCEP GFS via
the NOMADS GRIB filter service, subset to the Indian Ocean region only.

REQUIRES NETWORK ACCESS to nomads.ncep.noaa.gov (not available in this
sandbox -- verified: only pypi/npm/github domains are allowlisted here).
Run this from an environment with open internet access.

No authentication required (NOMADS GFS is public).

Docs: https://nomads.ncep.noaa.gov/  (GRIB Filter subsetting service)

Variables pulled: UGRD, VGRD @ 10 m above ground (10m wind components)

Pipeline:
    NOMADS GRIB filter (subset by region+variable+level)
        -> GRIB2 file (raw/noaa/)
        -> xarray + cfgrib
        -> derive wind_speed, wind_direction
        -> processed/weather/wind_grid.json

Run:
    python noaa_ingest.py --cycle 00 --forecast-hour 000
"""

import argparse
import json
import math
import os
from datetime import datetime, timezone

import requests

LAT_MIN, LAT_MAX = -32.0, 26.0
LON_MIN, LON_MAX = 25.0, 105.0

NOMADS_BASE = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"

RAW_DIR = "../raw/noaa"
OUT_PATH = "../processed/weather/wind_grid.json"


def build_nomads_url(date_str, cycle, fhour):
    """
    Builds a GRIB-filter URL that subsets GFS 0.25deg to our bounding box
    and only the 10m wind variables, for a single forecast hour.
    """
    params = {
        "file": f"gfs.t{cycle}z.pgrb2.0p25.f{fhour}",
        "lev_10_m_above_ground": "on",
        "var_UGRD": "on",
        "var_VGRD": "on",
        "subregion": "",
        "leftlon": str(LON_MIN),
        "rightlon": str(LON_MAX),
        "toplat": str(LAT_MAX),
        "bottomlat": str(LAT_MIN),
        "dir": f"/gfs.{date_str}/{cycle}/atmos",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{NOMADS_BASE}?{query}"


def download_grib(date_str, cycle, fhour):
    os.makedirs(RAW_DIR, exist_ok=True)
    url = build_nomads_url(date_str, cycle, fhour)
    out_file = os.path.join(RAW_DIR, f"gfs_{date_str}_{cycle}z_f{fhour}.grib2")

    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with open(out_file, "wb") as f:
        f.write(resp.content)
    return out_file


def process_grib_to_grid(grib_path):
    """Requires xarray + cfgrib + eccodes installed."""
    import xarray as xr

    ds = xr.open_dataset(grib_path, engine="cfgrib")
    u = ds["u10"]
    v = ds["v10"]

    cells = []
    now = datetime.now(timezone.utc).isoformat()
    lats = u.latitude.values
    lons = u.longitude.values

    for lat in lats:
        for lon in lons:
            uu = float(u.sel(latitude=lat, longitude=lon))
            vv = float(v.sel(latitude=lat, longitude=lon))
            speed = math.hypot(uu, vv)
            # meteorological "from" direction
            direction = (math.degrees(math.atan2(-uu, -vv))) % 360
            cells.append({
                "lat": round(float(lat), 3),
                "lon": round(float(lon), 3),
                "wind_speed": round(speed, 2),
                "wind_direction": round(direction, 1),
                "timestamp": now,
                "source": "NOAA",
                "data_status": "CACHED",
            })
    return cells


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.utcnow().strftime("%Y%m%d"))
    parser.add_argument("--cycle", default="00", choices=["00", "06", "12", "18"])
    parser.add_argument("--forecast-hour", default="000")
    args = parser.parse_args()

    print(f"Downloading GFS wind data for {args.date} {args.cycle}z f{args.forecast_hour} "
          f"(Indian Ocean subset lat[{LAT_MIN},{LAT_MAX}] lon[{LON_MIN},{LON_MAX}])...")
    grib_path = download_grib(args.date, args.cycle, args.forecast_hour)
    print(f"Saved raw GRIB2 to {grib_path}")

    cells = process_grib_to_grid(grib_path)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(cells, f)
    print(f"Wrote {len(cells)} wind cells to {OUT_PATH}")


if __name__ == "__main__":
    main()

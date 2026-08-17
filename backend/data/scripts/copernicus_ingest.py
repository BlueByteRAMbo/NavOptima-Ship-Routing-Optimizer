"""
copernicus_ingest.py
=====================
P0 source. Pulls ocean currents (U/V) and wave data from Copernicus Marine
Service via the official `copernicusmarine` Python toolbox, subset to the
Indian Ocean region only.

REQUIRES:
    pip install copernicusmarine
    Free Copernicus Marine account: https://marine.copernicus.eu
    Auth via env vars (do NOT hardcode credentials):
        COPERNICUSMARINE_SERVICE_USERNAME
        COPERNICUSMARINE_SERVICE_PASSWORD
    (or run `copernicusmarine login` once interactively, which caches creds)

REQUIRES NETWORK ACCESS to Copernicus Marine servers (not available in this
sandbox). Run from an environment with open internet access.

Datasets used (subject to team confirming exact IDs via `copernicusmarine describe`):
    Physics (currents):  GLOBAL_ANALYSISFORECAST_PHY_001_024
        variables: uo (eastward current), vo (northward current)
        depth: surface (~0.49m, the shallowest available layer -- we do NOT
        build a 3D ocean model, per spec section 11)
    Waves:  GLOBAL_ANALYSISFORECAST_WAV_001_027
        variables: VHM0 (significant wave height), VTPK (wave period)

Pipeline:
    copernicusmarine.subset(...)
        -> NetCDF (raw/copernicus/)
        -> xarray
        -> normalize
        -> processed/ocean/ocean_grid.json

Run:
    python copernicus_ingest.py
"""

import json
import os
from datetime import datetime, timezone, timedelta

LAT_MIN, LAT_MAX = -32.0, 26.0
LON_MIN, LON_MAX = 25.0, 105.0

RAW_DIR = "../raw/copernicus"
OUT_PATH = "../processed/ocean/ocean_grid.json"

PHYSICS_DATASET_ID = "cmems_mod_glo_phy_anfc_0.083deg_PT1H-m"  # currents (confirm via `describe`)
WAVES_DATASET_ID = "cmems_mod_glo_wav_anfc_0.083deg_PT3H-i"    # waves (confirm via `describe`)


def fetch_subset(dataset_id, variables, out_name):
    """Uses the official toolbox -- never a hand-rolled REST call."""
    import copernicusmarine

    os.makedirs(RAW_DIR, exist_ok=True)
    out_path = os.path.join(RAW_DIR, out_name)

    now = datetime.now(timezone.utc)
    copernicusmarine.subset(
        dataset_id=dataset_id,
        variables=variables,
        minimum_longitude=LON_MIN,
        maximum_longitude=LON_MAX,
        minimum_latitude=LAT_MIN,
        maximum_latitude=LAT_MAX,
        start_datetime=(now - timedelta(hours=3)).isoformat(),
        end_datetime=now.isoformat(),
        minimum_depth=0,
        maximum_depth=1,  # surface layer only -- no 3D ocean model
        output_filename=out_path,
        force_download=True,
    )
    return out_path


def normalize(currents_nc, waves_nc):
    import xarray as xr

    ds_cur = xr.open_dataset(currents_nc)
    ds_wav = xr.open_dataset(waves_nc)

    cells = []
    now = datetime.now(timezone.utc).isoformat()
    lats = ds_cur.latitude.values
    lons = ds_cur.longitude.values

    for lat in lats:
        for lon in lons:
            try:
                u = float(ds_cur["uo"].sel(latitude=lat, longitude=lon).isel(time=-1).values)
                v = float(ds_cur["vo"].sel(latitude=lat, longitude=lon).isel(time=-1).values)
                wh = float(ds_wav["VHM0"].sel(latitude=lat, longitude=lon, method="nearest").isel(time=-1).values)
                wp = float(ds_wav["VTPK"].sel(latitude=lat, longitude=lon, method="nearest").isel(time=-1).values)
            except Exception:
                continue  # missing/land cell, skip

            cells.append({
                "lat": round(float(lat), 3),
                "lon": round(float(lon), 3),
                "current_u": round(u, 3),
                "current_v": round(v, 3),
                "wave_height": round(wh, 2),
                "wave_period": round(wp, 1),
                "timestamp": now,
                "source": "Copernicus Marine",
                "data_status": "CACHED",
            })
    return cells


def main():
    print(f"Fetching Copernicus Marine currents+waves for Indian Ocean "
          f"lat[{LAT_MIN},{LAT_MAX}] lon[{LON_MIN},{LON_MAX}] (surface layer only)...")
    currents_nc = fetch_subset(PHYSICS_DATASET_ID, ["uo", "vo"], "currents.nc")
    waves_nc = fetch_subset(WAVES_DATASET_ID, ["VHM0", "VTPK"], "waves.nc")

    cells = normalize(currents_nc, waves_nc)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(cells, f)
    print(f"Wrote {len(cells)} ocean cells to {OUT_PATH}")


if __name__ == "__main__":
    main()

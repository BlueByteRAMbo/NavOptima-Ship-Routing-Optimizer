"""
gfw_ingest.py
=============
P2 source (optional). Derives an AIS-based traffic/activity-density signal
from the Global Fishing Watch API v3, for the Indian Ocean region.

IMPORTANT: this does NOT represent "all ships in the ocean" -- GFW's public
API surfaces AIS-visible fishing-vessel activity and related events/effort
datasets, not a complete AIS feed. Document this honestly wherever
traffic_density is displayed.

REQUIRES:
    GFW account + API token: https://globalfishingwatch.org/our-apis/
    Auth via env var (do NOT hardcode credentials):
        GFW_API_TOKEN

REQUIRES NETWORK ACCESS to gateway.api.globalfishingwatch.org (not available
in this sandbox).

Per spec section 17 (GFW fallback): if auth/access/time becomes a blocker,
STOP and use the mock fallback below -- do not let this block the demo.

Run:
    python gfw_ingest.py            # attempts real API
    python gfw_ingest.py --mock     # writes traffic_density_demo.json directly
"""

import argparse
import json
import math
import os
import random
from datetime import datetime, timezone

import requests

LAT_MIN, LAT_MAX = -32.0, 26.0
LON_MIN, LON_MAX = 25.0, 105.0
RESOLUTION_DEG = 1.0  # coarser than main env grid -- traffic signal is sparse

GFW_API_BASE = "https://gateway.api.globalfishingwatch.org/v3"
OUT_PATH = "../processed/traffic/traffic_grid.json"
MOCK_OUT_PATH = "../cache/traffic_density_demo.json"

random.seed(11)


def fetch_real(days=30):
    token = os.environ.get("GFW_API_TOKEN")
    if not token:
        raise RuntimeError("Missing GFW_API_TOKEN environment variable.")

    headers = {"Authorization": f"Bearer {token}"}
    # 4Wings apparent-fishing-effort endpoint, Indian Ocean bbox, daily bins
    url = f"{GFW_API_BASE}/4wings/report"
    params = {
        "spatial-resolution": "LOW",
        "temporal-resolution": "ENTIRE",
        "datasets[0]": "public-global-fishing-effort:latest",
        "date-range": f"{days}d",
        "bbox": f"{LON_MIN},{LAT_MIN},{LON_MAX},{LAT_MAX}",
    }
    resp = requests.get(url, headers=headers, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def normalize_real(raw):
    now = datetime.now(timezone.utc).isoformat()
    cells = []
    entries = raw.get("entries", []) if isinstance(raw, dict) else []
    for e in entries:
        try:
            lat, lon, value = e["lat"], e["lon"], e.get("value", 0)
        except (KeyError, TypeError):
            continue
        cells.append({
            "lat": round(float(lat), 3),
            "lon": round(float(lon), 3),
            "traffic_density": round(min(1.0, float(value) / 100.0), 3),
            "timestamp": now,
            "source": "Global Fishing Watch",
            "data_status": "CACHED",
            "note": "AIS-derived fishing-vessel activity signal, not total vessel traffic",
        })
    return cells


def build_mock():
    """Deterministic MOCK traffic surface: denser near the 15 known ports."""
    with open("../cache/ports.json") as f:
        ports = json.load(f)

    now = datetime.now(timezone.utc).isoformat()
    cells = []
    lat = LAT_MIN
    while lat <= LAT_MAX:
        lon = LON_MIN
        while lon <= LON_MAX:
            density = 0.03 + 0.05 * random.random()
            for p in ports:
                d = math.hypot(lat - p["lat"], lon - p["lon"])
                density += 0.4 * math.exp(-d / 2.5)
            cells.append({
                "lat": round(lat, 2),
                "lon": round(lon, 2),
                "traffic_density": round(min(1.0, density), 3),
                "timestamp": now,
                "source": "Global Fishing Watch (mock fallback)",
                "data_status": "MOCK",
                "note": "Simulated demo signal, port-proximity based -- not real AIS data",
            })
            lon += RESOLUTION_DEG
        lat += RESOLUTION_DEG
    return cells


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="skip real API, write mock data")
    args = parser.parse_args()

    if args.mock or not os.environ.get("GFW_API_TOKEN"):
        print("Using MOCK fallback for GFW traffic data (P2, per spec section 17).")
        cells = build_mock()
        out_path = MOCK_OUT_PATH
    else:
        print(f"Fetching GFW activity data for Indian Ocean bbox...")
        try:
            raw = fetch_real()
            cells = normalize_real(raw)
            out_path = OUT_PATH
        except Exception as ex:
            print(f"GFW real fetch failed ({ex}); falling back to MOCK per section 17.")
            cells = build_mock()
            out_path = MOCK_OUT_PATH

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(cells, f)
    print(f"Wrote {len(cells)} traffic cells to {out_path}")


if __name__ == "__main__":
    main()

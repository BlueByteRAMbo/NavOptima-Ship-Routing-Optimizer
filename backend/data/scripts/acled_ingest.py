"""
acled_ingest.py
================
P1 source. Pulls conflict/security events from the official ACLED API,
filtered to the Indian Ocean coastal region and a recent time window, and
converts them into spatial security-risk zones for the routing engine.

ACLED is a CONFLICT-EVENT dataset -- it is NOT a dedicated maritime piracy
API. It is used here as ONE input into a broader, simplified security-risk
model (per spec section 13/14). Do not oversell this as complete maritime
security intelligence.

REQUIRES:
    ACLED account + API key: https://acleddata.com/register/
    Auth via env vars (do NOT hardcode credentials):
        ACLED_API_KEY
        ACLED_EMAIL   (ACLED API requires the registered email as well)

REQUIRES NETWORK ACCESS to the ACLED API (not available in this sandbox).

Pipeline:
    ACLED REST API (region + date filtered)
        -> raw/acled/events.json
        -> filter to coastal/maritime-relevant region
        -> convert event -> {lat, lon, radius_km, severity}
        -> processed/security/security_events.json

Run:
    python acled_ingest.py --days 90
"""

import argparse
import json
import os
from datetime import datetime, timezone, timedelta

import requests

LAT_MIN, LAT_MAX = -32.0, 26.0
LON_MIN, LON_MAX = 25.0, 105.0

ACLED_API_URL = "https://api.acleddata.com/acled/read"
RAW_DIR = "../raw/acled"
OUT_PATH = "../processed/security/security_events.json"

# ACLED "fatalities" isn't a clean 0-1 severity signal by itself; this is a
# simple, documented, explainable proxy -- not a validated risk model.
def severity_from_event(event):
    fatalities = int(event.get("fatalities", 0) or 0)
    severity = min(1.0, 0.2 + 0.1 * fatalities)
    return round(severity, 2)


def fetch_events(days):
    api_key = os.environ.get("ACLED_API_KEY")
    email = os.environ.get("ACLED_EMAIL")
    if not api_key or not email:
        raise RuntimeError(
            "Missing ACLED_API_KEY / ACLED_EMAIL environment variables. "
            "Register at https://acleddata.com/register/"
        )

    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {
        "key": api_key,
        "email": email,
        "event_date": f"{start_date}|{datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "event_date_where": "BETWEEN",
        "latitude": f"{LAT_MIN}|{LAT_MAX}",
        "latitude_where": "BETWEEN",
        "longitude": f"{LON_MIN}|{LON_MAX}",
        "longitude_where": "BETWEEN",
        "limit": 2000,
    }
    resp = requests.get(ACLED_API_URL, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    os.makedirs(RAW_DIR, exist_ok=True)
    with open(os.path.join(RAW_DIR, "events_raw.json"), "w") as f:
        json.dump(data, f)

    return data.get("data", [])


def normalize(events):
    now = datetime.now(timezone.utc).isoformat()
    zones = []
    for e in events:
        try:
            lat = float(e["latitude"])
            lon = float(e["longitude"])
        except (KeyError, TypeError, ValueError):
            continue

        zones.append({
            "id": e.get("event_id_cnty", f"acled_{len(zones)}"),
            "type": "security",
            "lat": round(lat, 3),
            "lon": round(lon, 3),
            "radius_km": 75,  # simple fixed decay radius, documented assumption
            "severity": severity_from_event(e),
            "event_type": e.get("event_type"),
            "date": e.get("event_date"),
            "timestamp": now,
            "source": "ACLED",
            "data_status": "CACHED",
        })
    return zones


MOCK_OUT_PATH = "../cache/security_events.json"


def build_mock():
    """
    Illustrative MOCK security zones for the demo (NOT derived from ACLED).
    A mild bump near the Gulf of Aden / NW Indian Ocean approach, reflecting
    commonly-discussed maritime risk corridors -- for demo shape only.
    """
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "id": "mock_1",
            "type": "security",
            "lat": 12.5, "lon": 47.5,
            "radius_km": 200, "severity": 0.55,
            "event_type": "illustrative demo zone",
            "date": None,
            "timestamp": now,
            "source": "demo dataset (not ACLED)",
            "data_status": "MOCK",
        },
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--mock", action="store_true", help="skip real API, write mock zones")
    args = parser.parse_args()

    if args.mock or not (os.environ.get("ACLED_API_KEY") and os.environ.get("ACLED_EMAIL")):
        print("Using MOCK fallback for security zones (ACLED credentials not configured).")
        zones = build_mock()
        out_path = MOCK_OUT_PATH
    else:
        print(f"Fetching ACLED events for Indian Ocean coastal region, last {args.days} days...")
        events = fetch_events(args.days)
        zones = normalize(events)
        out_path = OUT_PATH

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(zones, f, indent=2)
    print(f"Wrote {len(zones)} security zones to {out_path}")


if __name__ == "__main__":
    main()

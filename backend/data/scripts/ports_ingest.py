"""
ports_ingest.py
================
Builds the canonical 15-port dataset for NavOptima (PSS07).

DATA STATUS: coordinates are curated from public geographic/port-authority
references (best-effort, NOT cross-checked against a live port-authority API
in this environment) -> data_status = "MOCK" for coordinates provenance note,
but coordinates themselves are realistic real-world values, safe for routing.
Congestion / waiting_hours are SIMULATED DEMO VALUES for the hackathon and
are explicitly NOT live operational data.

Run:
    python ports_ingest.py
Output:
    backend/data/cache/ports.json
"""

import json
import os
import random
from datetime import datetime, timezone

random.seed(42)  # deterministic demo values across runs

# id, name, country, lat, lon
# Coordinates are the port's approximate operational anchor point (main
# container terminal / harbor entrance), compiled from public geographic
# references. Recommend cross-checking against an official port authority
# / nautical chart source before any non-hackathon use.
PORTS_RAW = [
    ("mumbai",        "Mumbai",              "India",         18.9500, 72.9500),
    ("mundra",        "Mundra",              "India",         22.7395, 69.7076),
    ("kochi",         "Kochi",               "India",          9.9312, 76.2673),
    ("colombo",       "Colombo",             "Sri Lanka",      6.9500, 79.8400),
    ("chattogram",    "Chattogram",          "Bangladesh",    22.2800, 91.8300),
    ("yangon",        "Yangon / Thilawa",    "Myanmar",       16.6167, 96.2500),
    ("jebel_ali",     "Jebel Ali",           "UAE",           25.0118, 55.0618),
    ("salalah",       "Salalah",             "Oman",          17.0151, 54.0924),
    ("mombasa",       "Mombasa",             "Kenya",         -4.0435, 39.6682),
    ("dar_es_salaam", "Dar es Salaam",       "Tanzania",      -6.8235, 39.2695),
    ("port_louis",    "Port Louis",          "Mauritius",    -20.1609, 57.5012),
    ("durban",        "Durban",              "South Africa", -29.8587, 31.0218),
    ("singapore",     "Singapore",           "Singapore",      1.2900, 103.8500),
    ("port_klang",    "Port Klang",          "Malaysia",       2.9979, 101.3919),
    ("karachi",       "Karachi",             "Pakistan",      24.8482, 66.9931),
]

# Rough relative "busy-ness" tier used only to make demo congestion values
# look plausible (bigger transshipment hubs = higher baseline congestion).
BUSY_TIER = {
    "singapore": 0.85, "jebel_ali": 0.75, "port_klang": 0.70,
    "colombo": 0.65, "mumbai": 0.55, "karachi": 0.45,
    "chattogram": 0.60, "mundra": 0.40, "kochi": 0.35,
    "yangon": 0.50, "salalah": 0.40, "mombasa": 0.55,
    "dar_es_salaam": 0.50, "durban": 0.45, "port_louis": 0.30,
}


def build_ports():
    now = datetime.now(timezone.utc).isoformat()
    ports = []
    for pid, name, country, lat, lon in PORTS_RAW:
        base = BUSY_TIER.get(pid, 0.5)
        congestion = round(min(0.98, max(0.05, base + random.uniform(-0.1, 0.1))), 2)
        waiting_hours = round(congestion * random.uniform(20, 40), 1)
        ports.append({
            "id": pid,
            "name": name,
            "country": country,
            "lat": lat,
            "lon": lon,
            "type": "seaport",
            "congestion": congestion,
            "waiting_hours": waiting_hours,
            "utilization": round(min(0.99, congestion + random.uniform(-0.05, 0.05)), 2),
            "source": "curated static dataset (public geographic references) + simulated congestion",
            "data_status": "MOCK",
            "timestamp": now,
        })
    return ports


if __name__ == "__main__":
    ports = build_ports()
    ids = [p["id"] for p in ports]
    assert len(ids) == 15, f"expected 15 ports, got {len(ids)}"
    assert len(set(ids)) == 15, "duplicate port ids"
    for p in ports:
        assert -90 <= p["lat"] <= 90 and -180 <= p["lon"] <= 180, f"bad coords {p}"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_file = os.path.abspath(os.path.join(script_dir, "..", "cache", "ports.json"))
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(ports, f, indent=2)
    print(f"Wrote {len(ports)} ports to {cache_file}")

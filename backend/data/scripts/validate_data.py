"""
validate_data.py
=================
Runs the checklist from spec section 29 against the cached data outputs.
Exit code 0 = all pass, 1 = failures found (prints details either way).

Run:
    python validate_data.py
"""

import json
import math
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "cache"))

failures = []
passes = []


def check(name, condition):
    if condition:
        passes.append(name)
    else:
        failures.append(name)


def main():
    ports_path = os.path.join(CACHE_DIR, "ports.json")
    env_path = os.path.join(CACHE_DIR, "environment.json")
    with open(ports_path, encoding="utf-8") as f:
        ports = json.load(f)
    with open(env_path, encoding="utf-8") as f:
        env = json.load(f)

    # -- Ports --
    check("all 15 ports present", len(ports) == 15)
    ids = [p["id"] for p in ports]
    check("no duplicate port ids", len(ids) == len(set(ids)))
    check(
        "all ports have valid coordinates",
        all(-90 <= p["lat"] <= 90 and -180 <= p["lon"] <= 180 for p in ports),
    )
    required_port_fields = {"id", "name", "country", "lat", "lon", "congestion",
                             "waiting_hours", "source", "timestamp", "data_status"}
    check(
        "all ports have required fields",
        all(required_port_fields.issubset(p.keys()) for p in ports),
    )
    check(
        "no impossible NaN/Inf in port congestion/waiting_hours",
        all(math.isfinite(p["congestion"]) and math.isfinite(p["waiting_hours"]) for p in ports),
    )

    # -- Environment grid --
    check("environment grid non-empty", len(env) > 0)
    required_env_fields = {"lat", "lon", "is_ocean", "wind_speed", "wind_direction",
                            "wave_height", "wave_period", "current_u", "current_v",
                            "security_risk", "traffic_density", "timestamp", "sources"}
    check(
        "no missing required environment fields",
        all(required_env_fields.issubset(c.keys()) for c in env),
    )
    check(
        "lat/lon ranges valid in grid",
        all(-90 <= c["lat"] <= 90 and -180 <= c["lon"] <= 180 for c in env),
    )
    check("ocean mask present (is_ocean)", all("is_ocean" in c for c in env))
    check(
        "security_risk normalized 0-1",
        all(0.0 <= c["security_risk"] <= 1.0 for c in env),
    )
    check(
        "traffic_density normalized 0-1",
        all(0.0 <= c["traffic_density"] <= 1.0 for c in env),
    )
    check(
        "no NaN/Inf in numeric env fields",
        all(
            all(math.isfinite(c[k]) for k in
                ["wind_speed", "wind_direction", "wave_height", "wave_period",
                 "current_u", "current_v", "security_risk", "traffic_density"])
            for c in env
        ),
    )
    check("source metadata present in every cell", all(c.get("sources") for c in env))

    # -- Grid covers all ports (nearest cell within reasonable distance) --
    def nearest_dist(port):
        return min(
            math.hypot(port["lat"] - c["lat"], port["lon"] - c["lon"]) for c in env
        )

    max_gap = max(nearest_dist(p) for p in ports)
    check(f"environment grid covers all ports (max gap {max_gap:.2f} deg < 1.0)", max_gap < 1.0)

    # -- Report --
    print(f"PASS ({len(passes)}):")
    for p in passes:
        print(f"  [x] {p}")
    if failures:
        print(f"\nFAIL ({len(failures)}):")
        for f in failures:
            print(f"  [ ] {f}")
        sys.exit(1)
    else:
        print("\nAll validation checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()

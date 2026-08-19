"""
Live Server Verification Script
Starts uvicorn backend.app.main:app, tests all endpoints with HTTP requests, and validates response schemas.
"""
import subprocess
import time
import requests
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    print("Starting uvicorn server on http://127.0.0.1:8000...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--port", "8000", "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for server to boot
        time.sleep(2)
        base_url = "http://127.0.0.1:8000/api"

        # 1. Health
        r = requests.get(f"{base_url}/health")
        assert r.status_code == 200, f"Health failed: {r.status_code}"
        print(f"[OK] GET /api/health -> {r.json()}")

        # 2. Ports
        r = requests.get(f"{base_url}/ports")
        assert r.status_code == 200
        ports = r.json()
        assert len(ports) == 20
        print(f"[OK] GET /api/ports -> {len(ports)} ports loaded")

        # 3. Environment
        r = requests.get(f"{base_url}/environment?limit=5")
        assert r.status_code == 200
        cells = r.json()
        assert len(cells) == 5
        print(f"[OK] GET /api/environment?limit=5 -> {len(cells)} cells returned")

        # 4. Data sources
        r = requests.get(f"{base_url}/data-sources")
        assert r.status_code == 200
        sources = r.json()
        print(f"[OK] GET /api/data-sources -> {len(sources)} sources returned")

        # 5. Route: Mumbai -> Colombo (Balanced)
        route_req = {
            "origin": "mumbai",
            "destination": "colombo",
            "ship": "container",
            "optimization": "balanced",
        }
        r = requests.post(f"{base_url}/route", json=route_req)
        assert r.status_code == 200
        route = r.json()
        print(f"[OK] POST /api/route (Mumbai -> Colombo) -> Dist: {route['distance_km']}km, ETA: {route['eta_hours']}h, Fuel: {route['fuel_mt']}mt, Safety: {route['safety_score']}")
        print(f"     Reason: {route['reason']}")

        # 6. Route: Mumbai -> Singapore (Fastest)
        route_req2 = {
            "origin": "mumbai",
            "destination": "singapore",
            "ship": "container",
            "optimization": "fastest",
        }
        r = requests.post(f"{base_url}/route", json=route_req2)
        assert r.status_code == 200
        route2 = r.json()
        print(f"[OK] POST /api/route (Mumbai -> Singapore) -> Dist: {route2['distance_km']}km, ETA: {route2['eta_hours']}h, Fuel: {route2['fuel_mt']}mt")

        # 7. Simulation Event: Tropical storm in Arabian Sea
        sim_req = {
            "type": "storm",
            "lat": 12.0,
            "lon": 75.0,
            "radius_km": 150,
            "severity": 0.9,
            "label": "Tropical Storm — Arabian Sea"
        }
        r = requests.post(f"{base_url}/simulation/event", json=sim_req)
        assert r.status_code == 200
        sim = r.json()
        print(f"[OK] POST /api/simulation/event -> ETA change: +{sim['eta_change_hours']}h, Fuel change: +{sim['fuel_change_mt']}mt, Safety change: +{sim['safety_change']}")
        print(f"     Reason: {sim['reason']}")

        print("\nAll live HTTP endpoint verifications passed successfully!")

    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()

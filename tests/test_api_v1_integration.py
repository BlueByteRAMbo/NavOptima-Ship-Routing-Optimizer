"""
Integration tests for NavOptima FastAPI v1 REST API
"""
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_ports_endpoint():
    res = client.get("/api/v1/ports")
    assert res.status_code == 200
    ports = res.json()
    assert len(ports) == 15
    mumbai = next(p for p in ports if p["id"] == "mumbai")
    assert mumbai["supported_in_routing"] is True


def test_environment_endpoint():
    res = client.get("/api/v1/environment?limit=10")
    assert res.status_code == 200
    cells = res.json()
    assert len(cells) <= 10


def test_data_sources_endpoint():
    res = client.get("/api/v1/data-sources")
    assert res.status_code == 200
    sources = res.json()
    assert len(sources) > 0


def test_four_strategies_routing():
    strategies = ["FASTEST", "SAFEST", "LEAST_CONGESTED", "BALANCED"]
    for strat in strategies:
        res = client.post("/api/v1/route", json={
            "origin": "mumbai",
            "destination": "singapore",
            "ship": "container",
            "optimization": strat,
            "data_mode": "HYBRID"
        })
        assert res.status_code == 200, f"Strategy {strat} failed"
        data = res.json()
        assert data["routing_supported"] is True
        assert len(data["coordinates"]) > 0
        assert data["strategy"] == strat
        assert data["data_mode"] == "HYBRID"


def test_unsupported_port_routing():
    res = client.post("/api/v1/route", json={
        "origin": "durban",
        "destination": "mumbai",
        "ship": "container",
        "optimization": "BALANCED",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["routing_supported"] is False
    assert len(data["coordinates"]) == 0


def test_voyage_lifecycle_api():
    # 1. Create voyage
    res = client.post("/api/v1/voyages", json={
        "origin": "mumbai",
        "destination": "singapore",
        "ship": "container",
        "optimization": "BALANCED",
        "data_mode": "HYBRID",
    })
    assert res.status_code == 200
    voyage = res.json()
    voyage_id = voyage["voyage_id"]
    assert voyage_id is not None

    # 2. Get voyage state
    res_get = client.get(f"/api/v1/voyages/{voyage_id}")
    assert res_get.status_code == 200
    assert res_get.json()["voyage_id"] == voyage_id

    # 3. Tick voyage
    res_tick = client.post(f"/api/v1/voyages/{voyage_id}/tick", json={"tick_duration": 1.0})
    assert res_tick.status_code == 200
    assert res_tick.json()["current_time"] == 1.0

    # 4. Get route
    res_route = client.get(f"/api/v1/voyages/{voyage_id}/route")
    assert res_route.status_code == 200
    assert len(res_route.json()["coordinates"]) > 0


def test_simulation_event_api():
    res = client.post("/api/v1/simulation/event", json={
        "type": "storm",
        "lat": 12.0,
        "lon": 75.0,
        "radius_km": 150,
        "severity": 0.9,
        "label": "Test Storm"
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["old_route"]) > 0
    assert len(data["new_route"]) > 0

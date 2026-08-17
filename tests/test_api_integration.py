"""
Integration Test Suite for NavOptima FastAPI Backend
Tests all API endpoints, data integration, and frozen routing engine execution.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    """GET /api/health returns status 200 and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_ports_endpoint():
    """GET /api/ports returns all 15 canonical ports."""
    response = client.get("/api/ports")
    assert response.status_code == 200
    ports = response.json()
    assert isinstance(ports, list)
    assert len(ports) == 15

    # Check key port exists and has required fields
    mumbai = next((p for p in ports if p["id"] == "mumbai"), None)
    assert mumbai is not None
    assert mumbai["name"] == "Mumbai"
    assert mumbai["lat"] > 0
    assert mumbai["lon"] > 0
    assert "congestion" in mumbai
    assert "waiting_hours" in mumbai
    assert "supported_in_routing" in mumbai
    assert mumbai["supported_in_routing"] is True


def test_environment_endpoint():
    """GET /api/environment returns real environment cells."""
    response = client.get("/api/environment?limit=10")
    assert response.status_code == 200
    cells = response.json()
    assert isinstance(cells, list)
    assert len(cells) == 10
    c0 = cells[0]
    assert "lat" in c0
    assert "lon" in c0
    assert "current_u" in c0
    assert "wave_height" in c0


def test_data_sources_endpoint():
    """GET /api/data-sources returns data source metadata with honest tags."""
    response = client.get("/api/data-sources")
    assert response.status_code == 200
    sources = response.json()
    assert isinstance(sources, list)
    assert len(sources) >= 4

    copernicus = next((s for s in sources if s["source"] == "Copernicus Marine"), None)
    assert copernicus is not None
    assert copernicus["status"] in ("CACHED", "LIVE", "MOCK")


def test_route_calculation_mumbai_colombo():
    """POST /api/route computes optimal route for Mumbai -> Colombo."""
    payload = {
        "origin": "mumbai",
        "destination": "colombo",
        "ship": "container",
        "optimization": "balanced",
    }
    response = client.post("/api/route", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "coordinates" in data
    assert len(data["coordinates"]) >= 2
    assert "distance_km" in data
    assert data["distance_km"] > 500
    assert "eta_hours" in data
    assert data["eta_hours"] > 0
    assert "fuel_mt" in data
    assert data["fuel_mt"] > 0
    assert "safety_score" in data
    assert 0 <= data["safety_score"] <= 100
    assert "reason" in data


def test_route_calculation_mumbai_singapore():
    """POST /api/route computes multi-waypoint route for Mumbai -> Singapore."""
    payload = {
        "origin": "mumbai",
        "destination": "singapore",
        "ship": "container",
        "optimization": "fastest",
    }
    response = client.post("/api/route", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["coordinates"]) >= 4
    assert data["distance_km"] > 3000
    assert data["eta_hours"] > 50


def test_simulation_event():
    """POST /api/simulation/event evaluates dynamic disruption and reroutes."""
    payload = {
        "type": "storm",
        "lat": 12.0,
        "lon": 75.0,
        "radius_km": 150,
        "severity": 0.9,
        "label": "Arabian Sea Tropical Storm",
    }
    response = client.post("/api/simulation/event", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "old_route" in data
    assert "new_route" in data
    assert len(data["old_route"]) > 0
    assert len(data["new_route"]) > 0
    assert "reason" in data
    assert "eta_change_hours" in data
    assert "fuel_change_mt" in data
    assert "safety_change" in data

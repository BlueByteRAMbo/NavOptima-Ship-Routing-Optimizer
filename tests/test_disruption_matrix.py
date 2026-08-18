"""
Automated Disruption Test Matrix (Part 15)
Tests:
Routes:
- Mumbai -> Singapore
- Mumbai -> Kochi
- Mumbai -> Colombo
- Colombo -> Singapore

Disruptions:
- no disruption (baseline)
- tropical storm
- port congestion
- security threat
"""
import pytest
from backend.app.orchestration.optimizer_service import (
    create_voyage,
    handle_simulation_event,
)
from backend.app.models.route import (
    VoyageCreateRequest,
    SimulationEvent,
)

ROUTES = [
    ("mumbai", "singapore"),
    ("mumbai", "kochi"),
    ("mumbai", "colombo"),
    ("colombo", "singapore"),
]

EVENTS = [
    {"type": "storm", "lat": 12.0, "lon": 75.0, "radius_km": 150.0, "severity": 0.9, "label": "Arabian Sea Storm"},
    {"type": "port_congestion", "lat": 6.95, "lon": 79.84, "radius_km": 50.0, "severity": 0.85, "label": "Colombo Congestion"},
    {"type": "security", "lat": 12.5, "lon": 47.5, "radius_km": 200.0, "severity": 0.75, "label": "Gulf of Aden Alert"},
]


@pytest.mark.parametrize("orig,dest", ROUTES)
@pytest.mark.parametrize("event_data", EVENTS)
def test_disruption_matrix(orig, dest, event_data):
    # 1. Create Voyage
    req = VoyageCreateRequest(
        origin=orig,
        destination=dest,
        ship="container",
        optimization="BALANCED",
        data_mode="HYBRID",
    )
    voyage = create_voyage(req)

    # 2. Trigger Disruption Event
    event = SimulationEvent(
        voyage_id=voyage.voyage_id,
        type=event_data["type"],
        lat=event_data["lat"],
        lon=event_data["lon"],
        radius_km=event_data["radius_km"],
        severity=event_data["severity"],
        label=event_data["label"],
    )

    resp = handle_simulation_event(event)

    # 3. Assertions
    assert resp.origin.lower() == orig
    assert resp.destination.lower() == dest
    assert len(resp.old_route) > 0
    assert len(resp.new_route) > 0
    assert resp.reason != ""

    if not resp.spatially_relevant:
        assert resp.rerouted is False
        assert resp.eta_change_hours == 0.0
        assert resp.fuel_change_mt == 0.0
        assert any(phrase in resp.reason.lower() for phrase in ["spatially distant", "threshold", "does not intersect", "unaffected"])


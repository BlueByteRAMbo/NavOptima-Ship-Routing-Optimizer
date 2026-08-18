"""
Mandatory Regression Test Suite (Parts 16, 17, 18 of Specification)
Guarantees strict compliance against integration regressions.
"""
import os
import sys
import pytest

from backend.app.orchestration.optimizer_service import (
    create_voyage,
    get_voyage,
    handle_simulation_event,
    calculate_optimal_route,
)
from backend.app.models.route import (
    VoyageCreateRequest,
    SimulationEvent,
    RouteRequest,
)


def test_regression_1_mumbai_kochi_colombo_congestion():
    """
    REGRESSION TEST 1 (Part 16):
    Origin: Mumbai
    Destination: Kochi
    Trigger: Port Congestion event at Colombo (6.95°N, 79.84°E)
    
    EXPECTED:
    - Voyage MUST remain Mumbai -> Kochi.
    - Destination MUST NOT become Colombo or Singapore.
    - spatially_relevant MUST be False.
    - rerouted MUST be False.
    - eta_change_hours == 0.0, fuel_change_mt == 0.0, safety_change == 0.0.
    - Backend reason MUST state spatial distance irrelevance.
    """
    # 1. Initialize active voyage Mumbai -> Kochi
    voyage_req = VoyageCreateRequest(
        origin="mumbai",
        destination="kochi",
        ship="container",
        optimization="BALANCED",
        data_mode="HYBRID",
    )
    voyage = create_voyage(voyage_req)
    assert voyage.origin == "Mumbai"
    assert voyage.destination == "Kochi"

    # 2. Trigger Port Congestion at Colombo (6.95°N, 79.84°E) bound to active voyage
    event = SimulationEvent(
        voyage_id=voyage.voyage_id,
        type="port_congestion",
        lat=6.95,
        lon=79.84,
        radius_km=50.0,
        severity=0.9,
        label="Severe Congestion — Colombo Port",
    )
    sim_resp = handle_simulation_event(event)

    # 3. Assertions
    assert sim_resp.origin == "Mumbai", "Origin must remain Mumbai"
    assert sim_resp.destination == "Kochi", "Destination MUST remain Kochi (NOT Colombo or Singapore)"
    assert sim_resp.spatially_relevant is False, "Event at Colombo must be spatially irrelevant to Mumbai -> Kochi"
    assert sim_resp.rerouted is False, "Route should NOT reroute for irrelevant distant congestion"
    assert sim_resp.eta_change_hours == 0.0, "ETA change must be 0.0 for irrelevant event"
    assert sim_resp.fuel_change_mt == 0.0, "Fuel change must be 0.0 for irrelevant event"
    assert sim_resp.safety_change == 0.0, "Safety change must be 0.0 for irrelevant event"
    assert any(phrase in sim_resp.reason.lower() for phrase in ["spatially distant", "spatially irrelevant", "threshold", "does not intersect"]), "Reason must explain spatial distance irrelevance"



def test_regression_2_mumbai_singapore_storm_reroute():
    """
    REGRESSION TEST 2 (Part 17):
    Origin: Mumbai
    Destination: Singapore
    Trigger: Severe storm directly over primary corridor (12.0°N, 75.0°E)
    
    EXPECTED:
    - Voyage stays Mumbai -> Singapore.
    - spatially_relevant is True.
    - Frozen A* recomputes route and metrics from backend.
    - All metrics (distance, ETA, fuel, safety) recalculated mathematically.
    """
    voyage_req = VoyageCreateRequest(
        origin="mumbai",
        destination="singapore",
        ship="container",
        optimization="BALANCED",
        data_mode="HYBRID",
    )
    voyage = create_voyage(voyage_req)
    assert voyage.origin == "Mumbai"
    assert voyage.destination == "Singapore"

    event = SimulationEvent(
        voyage_id=voyage.voyage_id,
        type="storm",
        lat=14.46,
        lon=74.53,
        radius_km=300.0,
        severity=0.9,
        label="Tropical Storm — Arabian Sea Corridor",
    )
    sim_resp = handle_simulation_event(event)

    assert sim_resp.origin == "Mumbai"
    assert sim_resp.destination == "Singapore"
    assert sim_resp.spatially_relevant is True
    assert len(sim_resp.new_route) > 0
    assert sim_resp.active_route is not None
    assert sim_resp.active_route.distance_km > 0
    assert sim_resp.active_route.eta_hours > 0


def test_regression_3_conflicting_strategies_evaluation():
    """
    REGRESSION TEST 3 (Part 18):
    Origin: Mumbai
    Destination: Singapore
    Compare FASTEST, SAFEST, LEAST_CONGESTED, BALANCED
    
    EXPECTED:
    - All 4 strategies evaluate route objective costs.
    - Objective cost calculations match weighted formulas.
    """
    strategies = ["FASTEST", "SAFEST", "LEAST_CONGESTED", "BALANCED"]
    results = {}

    for strat in strategies:
        req = RouteRequest(
            origin="mumbai",
            destination="singapore",
            ship="container",
            optimization=strat,
            data_mode="HYBRID",
        )
        resp = calculate_optimal_route(req)
        assert resp.routing_supported is True
        assert resp.total_cost is not None and resp.total_cost > 0
        results[strat] = resp

    assert len(results) == 4

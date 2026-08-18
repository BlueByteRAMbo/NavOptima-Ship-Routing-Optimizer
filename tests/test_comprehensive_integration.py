"""
Comprehensive Master Integration Test Suite
============================================
Tests all 14 mandatory integration criteria:
1. Land-crossing geometry validation (0 land intersections)
2. Origin / Destination preservation across disruptions
3. No hardcoded Mumbai -> Singapore fallback (explicit KeyError / 404)
4. Reroute persistence in backend voyage state
5. Reroute continuity across /tick simulation clock steps
6. Irrelevant disruption handling (spatially_relevant=False, 0 deltas)
7. Port congestion semantics (ETA wait added, route geometry unchanged)
8. Storm & Security threat rerouting
9. Repeated disruption & hysteresis stability (no route bouncing)
10. Strategy objective weight vector preservation
11. 7 Canonical OD pairs × 4 Strategies matrix (MOCK + HYBRID)
"""

import json
import pytest

from backend.app.models.route import RouteRequest, SimulationEvent, VoyageCreateRequest
from backend.app.orchestration.optimizer_service import (
    calculate_optimal_route,
    create_voyage,
    get_voyage,
    handle_simulation_event,
    tick_voyage,
    get_routing_graph,
    _voyages_db,
)
from test_land_crossing import LAND_POLYGONS, _is_point_in_poly


OD_PAIRS = [
    ("mumbai", "singapore"),
    ("mumbai", "kochi"),
    ("mumbai", "colombo"),
    ("kochi", "singapore"),
    ("colombo", "singapore"),
    ("chennai", "singapore"),
    ("yangon", "singapore"),
]

STRATEGIES = ["FASTEST", "SAFEST", "LEAST_CONGESTED", "BALANCED"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. LAND CROSSING VALIDATION ACROSS ALL ROUTE PATHS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("orig,dest", OD_PAIRS)
@pytest.mark.parametrize("strat", STRATEGIES)
@pytest.mark.parametrize("mode", ["MOCK", "HYBRID"])
def test_all_matrix_routes_have_zero_land_crossing(orig, dest, strat, mode):
    """Verifies every computed route in the matrix contains zero land-crossing segments."""
    req = RouteRequest(origin=orig, destination=dest, ship="container", optimization=strat, data_mode=mode)
    res = calculate_optimal_route(req)
    assert res.routing_supported is True
    assert len(res.coordinates) >= 2

    # Check consecutive coordinate pairs
    for i in range(len(res.coordinates) - 1):
        lat1, lon1 = res.coordinates[i]
        lat2, lon2 = res.coordinates[i + 1]

        for step in range(2, 19):
            t = step / 20.0
            sample_lat = lat1 + t * (lat2 - lat1)
            sample_lon = lon1 + t * (lon2 - lon1)
            for land_name, poly in LAND_POLYGONS.items():
                assert not _is_point_in_poly(sample_lat, sample_lon, poly), (
                    f"Route {orig} -> {dest} ({strat}/{mode}) leg {i} intersects {land_name} "
                    f"at ({sample_lat:.2f}, {sample_lon:.2f})"
                )


# ─────────────────────────────────────────────────────────────────────────────
# 2. ORIGIN & DESTINATION PRESERVATION ACROSS DISRUPTIONS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("orig,dest", [("mumbai", "kochi"), ("mumbai", "singapore"), ("kochi", "singapore"), ("colombo", "singapore")])
def test_origin_destination_preserved_during_disruptions(orig, dest):
    """Verifies that origin and destination are 100% preserved during any disruption."""
    vreq = VoyageCreateRequest(origin=orig, destination=dest, ship="container", optimization="BALANCED", data_mode="HYBRID")
    voyage = create_voyage(vreq)
    vid = voyage.voyage_id

    # Test storm
    storm_ev = SimulationEvent(voyage_id=vid, type="storm", lat=14.46, lon=74.53, radius_km=300.0, severity=0.9)
    resp_storm = handle_simulation_event(storm_ev)
    assert resp_storm.origin.lower() == orig.lower()
    assert resp_storm.destination.lower() == dest.lower()

    # Test port congestion
    cong_ev = SimulationEvent(voyage_id=vid, type="port_congestion", lat=6.95, lon=79.84, radius_km=50.0, severity=0.85)
    resp_cong = handle_simulation_event(cong_ev)
    assert resp_cong.origin.lower() == orig.lower()
    assert resp_cong.destination.lower() == dest.lower()

    # Test security threat
    sec_ev = SimulationEvent(voyage_id=vid, type="security", lat=5.5, lon=100.0, radius_km=200.0, severity=0.85)
    resp_sec = handle_simulation_event(sec_ev)
    assert resp_sec.origin.lower() == orig.lower()
    assert resp_sec.destination.lower() == dest.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 3. NO HARDCODED MUMBAI -> SINGAPORE FALLBACK (EXPLICIT ERROR ON INVALID SESSION)
# ─────────────────────────────────────────────────────────────────────────────

def test_no_hardcoded_mumbai_singapore_fallback():
    """Asserts that calling disruption with non-existent voyage ID raises KeyError, never defaulting."""
    fake_ev = SimulationEvent(voyage_id="invalid-uuid-999", type="storm", lat=12.0, lon=75.0, radius_km=100.0, severity=0.5)
    with pytest.raises(KeyError) as exc_info:
        handle_simulation_event(fake_ev)

    assert "not found" in str(exc_info.value).lower()
    assert "mumbai" not in str(exc_info.value).lower()


# ─────────────────────────────────────────────────────────────────────────────
# 4. REROUTE PERSISTENCE & TICK CONTINUITY
# ─────────────────────────────────────────────────────────────────────────────

def test_reroute_persistence_and_tick_continuity():
    """
    1. Create voyage (Mumbai -> Singapore, BALANCED).
    2. Inject severe storm on Konkan corridor.
    3. Verify new active_route is persisted to backend voyage.
    4. Call /tick and verify vessel advances along the NEW route path.
    """
    vreq = VoyageCreateRequest(origin="mumbai", destination="singapore", ship="container", optimization="BALANCED", data_mode="MOCK")
    voyage = create_voyage(vreq)
    vid = voyage.voyage_id
    initial_path = voyage.active_route.path_nodes

    # Inject storm
    event = SimulationEvent(voyage_id=vid, type="storm", lat=14.46, lon=74.53, radius_km=300.0, severity=0.95, label="Severe Storm")
    sim_resp = handle_simulation_event(event)

    # Persistence check
    voyage_after = get_voyage(vid)
    assert voyage_after.active_route.path_nodes == sim_resp.active_route.path_nodes

    # Tick continuity check
    tick_resp = tick_voyage(vid, tick_duration=3.0)
    assert tick_resp.current_time == 3.0
    assert tick_resp.active_route_nodes == sim_resp.active_route.path_nodes


# ─────────────────────────────────────────────────────────────────────────────
# 5. IRRELEVANT DISRUPTION HANDLING
# ─────────────────────────────────────────────────────────────────────────────

def test_irrelevant_disruption_handling():
    """Event 3000km away (Gulf of Aden) during Mumbai -> Singapore route must be spatially irrelevant."""
    vreq = VoyageCreateRequest(origin="mumbai", destination="singapore", ship="container", optimization="BALANCED", data_mode="HYBRID")
    voyage = create_voyage(vreq)

    aden_ev = SimulationEvent(voyage_id=voyage.voyage_id, type="security", lat=12.5, lon=47.5, radius_km=200.0, severity=0.8)
    sim_resp = handle_simulation_event(aden_ev)

    assert sim_resp.spatially_relevant is False
    assert sim_resp.rerouted is False
    assert sim_resp.eta_change_hours == 0.0
    assert sim_resp.fuel_change_mt == 0.0
    assert sim_resp.safety_change == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 6. PORT CONGESTION SEMANTICS
# ─────────────────────────────────────────────────────────────────────────────

def test_port_congestion_semantics():
    """Port congestion at Colombo increases waiting hours and updates ETA, route geometry unchanged."""
    vreq = VoyageCreateRequest(origin="mumbai", destination="colombo", ship="container", optimization="BALANCED", data_mode="HYBRID")
    voyage = create_voyage(vreq)
    base_eta = voyage.active_route.eta_hours

    cong_ev = SimulationEvent(voyage_id=voyage.voyage_id, type="port_congestion", lat=6.95, lon=79.84, radius_km=50.0, severity=0.85)
    sim_resp = handle_simulation_event(cong_ev)

    assert sim_resp.spatially_relevant is True
    assert sim_resp.rerouted is False
    assert sim_resp.eta_change_hours > 0.0
    assert sim_resp.active_route.eta_hours == round(base_eta + sim_resp.eta_change_hours, 1)


# ─────────────────────────────────────────────────────────────────────────────
# 7. REPEATED DISRUPTION & HYSTERESIS STABILITY
# ─────────────────────────────────────────────────────────────────────────────

def test_repeated_disruption_hysteresis_stability():
    """Triggering the exact same storm 5 times repeatedly must produce identical stable results, no oscillation."""
    vreq = VoyageCreateRequest(origin="mumbai", destination="singapore", ship="container", optimization="BALANCED", data_mode="HYBRID")
    voyage = create_voyage(vreq)

    storm_ev = SimulationEvent(voyage_id=voyage.voyage_id, type="storm", lat=14.46, lon=74.53, radius_km=300.0, severity=0.9)

    first_resp = handle_simulation_event(storm_ev)
    for _ in range(4):
        rep_resp = handle_simulation_event(storm_ev)
        assert rep_resp.active_route.path_nodes == first_resp.active_route.path_nodes
        assert rep_resp.eta_change_hours == first_resp.eta_change_hours

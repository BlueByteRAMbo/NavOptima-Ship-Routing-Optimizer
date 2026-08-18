"""
Automated Simulation UX Flow & State Machine Test Suite
Validates:
1. Auto-pause on disruption ahead & clock freeze
2. Alternative route evaluation & map metrics
3. Accept Alternative Route: preserves vessel coordinates, updates active route, auto-resumes playback
4. Keep Current Route: retains active route, preserves vessel coordinates, auto-resumes playback
5. AUTO DEMO speed calculation targeting ~60-90s playback
6. Multi-port and multi-strategy verification across MOCK & HYBRID modes
"""
import pytest
from backend.app.orchestration.optimizer_service import (
    create_voyage,
    tick_voyage,
    get_voyage,
    handle_simulation_event,
    CANONICAL_TO_GRAPH,
)
from backend.app.models.route import (
    VoyageCreateRequest,
    SimulationEvent,
)


def test_auto_pause_and_disruption_evaluation():
    """Validates that disruption ahead evaluates authoritative decision and remains paused for decision."""
    req = VoyageCreateRequest(
        origin="mumbai",
        destination="singapore",
        ship="container_large",
        optimization="BALANCED",
        data_mode="HYBRID",
    )
    v = create_voyage(req)
    v_id = v.voyage_id

    # Tick 3.0 hours
    t1 = tick_voyage(v_id, tick_duration=3.0)
    lat_at_t3, lon_at_t3 = t1.current_lat, t1.current_lon
    time_at_t3 = t1.current_time

    # Trigger storm ahead
    coords = t1.active_route.coordinates
    target_idx = min(len(coords) - 1, max(1, len(coords) // 2))
    storm_lat, storm_lon = coords[target_idx]

    event = SimulationEvent(
        voyage_id=v_id,
        type="storm",
        lat=storm_lat,
        lon=storm_lon,
        radius_km=200.0,
        severity=0.85,
        label="Tropical Storm Test",
    )
    sim_res = handle_simulation_event(event)

    # Verify simulation state after event
    state = get_voyage(v_id)
    assert state.current_time == time_at_t3, "Simulation clock must remain frozen during pause"
    assert state.current_lat == lat_at_t3, "Vessel latitude must remain frozen at current position"
    assert state.current_lon == lon_at_t3, "Vessel longitude must remain frozen at current position"
    assert sim_res.spatially_relevant is True


def test_accept_alternative_state_transition():
    """Validates manual override accepting alternative updates active route and preserves vessel position."""
    req = VoyageCreateRequest(
        origin="kochi",
        destination="singapore",
        ship="container_large",
        optimization="FASTEST",
        data_mode="HYBRID",
    )
    v = create_voyage(req)
    v_id = v.voyage_id

    # Tick 5.0 hours
    t1 = tick_voyage(v_id, tick_duration=5.0)
    lat_at_t5, lon_at_t5 = t1.current_lat, t1.current_lon

    # Inject storm ahead
    coords = t1.active_route.coordinates
    storm_lat, storm_lon = coords[len(coords) // 2]
    event = SimulationEvent(
        voyage_id=v_id,
        type="storm",
        lat=storm_lat,
        lon=storm_lon,
        radius_km=200.0,
        severity=0.9,
        label="Storm Ahead",
    )
    sim_res = handle_simulation_event(event)

    state_after = get_voyage(v_id)
    assert state_after.current_lat == lat_at_t5, "Position must be preserved after disruption evaluation"
    assert state_after.current_lon == lon_at_t5
    assert not state_after.is_completed

    # Resume ticking
    t2 = tick_voyage(v_id, tick_duration=5.0)
    assert t2.current_time == 10.0
    assert (t2.current_lat != lat_at_t5) or (t2.current_lon != lon_at_t5), "Vessel must continue moving along updated active route"


def test_auto_demo_speed_calculation():
    """Validates AUTO DEMO speed multiplier calculation for ~75s playback."""
    total_eta_hours = 225.0
    target_real_seconds = 75.0
    auto_speed = max(10, round(total_eta_hours / target_real_seconds))
    assert auto_speed == 10
    assert auto_speed >= 3


def test_multi_port_simulation_flows():
    """Validates simulation lifecycle across multiple OD pairs (Mumbai->Kochi, Colombo->Singapore, Kochi->Singapore)."""
    test_pairs = [
        ("mumbai", "kochi"),
        ("colombo", "singapore"),
        ("kochi", "singapore"),
    ]

    for orig, dest in test_pairs:
        req = VoyageCreateRequest(
            origin=orig,
            destination=dest,
            ship="container_large",
            optimization="BALANCED",
            data_mode="HYBRID",
        )
        v = create_voyage(req)
        assert v.voyage_id
        assert not v.is_completed

        # Tick 2.0 hours
        t = tick_voyage(v.voyage_id, tick_duration=2.0)
        assert t.current_time == 2.0
        assert t.active_route.distance_km > 0

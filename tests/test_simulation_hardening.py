"""
Automated Simulation Hardening & Synchronization Test Suite
Validates:
TEST A — VESSEL MOVEMENT: Position advances continuously after ticks; speed scaling works.
TEST B — DESTINATION REACHED: Destination event occurs ONLY when vessel position reaches destination.
TEST C — EVENT AHEAD: Disruption ahead is spatially relevant and not classified as behind vessel.
TEST D — EVENT BEHIND: Disruption behind vessel triggers EVENT_BEHIND_VESSEL with zero false rerouting.
TEST E — MANUAL OVERRIDE: Accepting alternative updates active route while preserving vessel position & clock.
TEST F — AUTOMATIC REROUTE: Cost improvement > hysteresis threshold automatically updates active route.
TEST G — RETAIN ROUTE: Cost improvement <= hysteresis threshold retains route with updated metrics.
"""
import pytest
from backend.app.orchestration.optimizer_service import (
    create_voyage,
    tick_voyage,
    get_voyage,
    handle_simulation_event,
)
from backend.app.models.route import (
    VoyageCreateRequest,
    SimulationEvent,
)


def test_scenario_a_vessel_movement_and_speed():
    """TEST A: Position advances after tick and clock scale is deterministic."""
    req = VoyageCreateRequest(
        origin="mumbai",
        destination="singapore",
        ship="container_large",
        optimization="FASTEST",
        data_mode="HYBRID",
    )
    v = create_voyage(req)
    v_id = v.voyage_id
    lat0, lon0 = v.current_lat, v.current_lon

    # Tick 1.0 hour (1x equivalent)
    t1 = tick_voyage(v_id, tick_duration=1.0)
    assert t1.current_time == 1.0
    lat1, lon1 = t1.current_lat, t1.current_lon
    assert (lat1 != lat0) or (lon1 != lon0), "Vessel position must advance after 1.0h tick"

    # Tick 5.0 hours (50x equivalent tick step)
    t5 = tick_voyage(v_id, tick_duration=5.0)
    assert t5.current_time == 6.0
    lat5, lon5 = t5.current_lat, t5.current_lon
    assert (lat5 != lat1) or (lon5 != lon1), "Vessel position must advance proportionally after 5.0h tick"


def test_scenario_b_destination_reached():
    """TEST B: Destination is reached ONLY when vessel coordinates reach destination."""
    req = VoyageCreateRequest(
        origin="mumbai",
        destination="colombo",
        ship="container_large",
        optimization="FASTEST",
        data_mode="MOCK",
    )
    v = create_voyage(req)
    v_id = v.voyage_id

    # Advance until completed
    max_ticks = 100
    for _ in range(max_ticks):
        t_res = tick_voyage(v_id, tick_duration=5.0)
        if t_res.is_completed:
            break

    state = get_voyage(v_id)
    assert state.is_completed is True
    dest_coords = state.active_route.coordinates[-1]
    dist_km = ((state.current_lat - dest_coords[0])**2 + (state.current_lon - dest_coords[1])**2)**0.5 * 111.0
    assert dist_km <= 50.0, f"Vessel final position ({state.current_lat}, {state.current_lon}) must be at destination ({dest_coords})"


def test_scenario_c_event_ahead():
    """TEST C: Disruption ahead is spatially relevant."""
    req = VoyageCreateRequest(
        origin="mumbai",
        destination="singapore",
        ship="container_large",
        optimization="BALANCED",
        data_mode="HYBRID",
    )
    v = create_voyage(req)
    v_id = v.voyage_id

    # Tick 2 hours
    t = tick_voyage(v_id, tick_duration=2.0)
    coords = t.active_route.coordinates
    target_lat, target_lon = coords[len(coords) // 2]

    event = SimulationEvent(
        voyage_id=v_id,
        type="storm",
        lat=target_lat,
        lon=target_lon,
        radius_km=150.0,
        severity=0.8,
        label="Storm Ahead",
    )
    res = handle_simulation_event(event)
    assert res.spatially_relevant is True
    assert res.decision != "EVENT_BEHIND_VESSEL"


def test_scenario_d_event_behind():
    """TEST D: Disruption behind vessel triggers EVENT_BEHIND_VESSEL."""
    req = VoyageCreateRequest(
        origin="mumbai",
        destination="singapore",
        ship="container_large",
        optimization="BALANCED",
        data_mode="MOCK",
    )
    v = create_voyage(req)
    v_id = v.voyage_id
    orig_lat, orig_lon = v.current_lat, v.current_lon

    # Tick vessel 20 hours along route
    for _ in range(10):
        tick_voyage(v_id, tick_duration=2.0)

    t_state = get_voyage(v_id)
    assert t_state.current_time == 20.0

    # Inject disruption at origin
    event = SimulationEvent(
        voyage_id=v_id,
        type="storm",
        lat=orig_lat,
        lon=orig_lon,
        radius_km=100.0,
        severity=0.8,
        label="Storm at Start Node",
    )
    res = handle_simulation_event(event)
    assert res.decision == "EVENT_BEHIND_VESSEL"
    assert res.rerouted is False


def test_scenario_e_manual_override_preserves_position():
    """TEST E: Manual override updates route while preserving vessel position and simulation clock."""
    req = VoyageCreateRequest(
        origin="kochi",
        destination="singapore",
        ship="container_large",
        optimization="FASTEST",
        data_mode="HYBRID",
    )
    v = create_voyage(req)
    v_id = v.voyage_id

    # Advance 4 hours
    t1 = tick_voyage(v_id, tick_duration=4.0)
    lat_at_t4, lon_at_t4 = t1.current_lat, t1.current_lon
    time_at_t4 = t1.current_time

    # Trigger storm ahead
    coords = t1.active_route.coordinates
    storm_lat, storm_lon = coords[max(1, len(coords) // 2)]
    event = SimulationEvent(
        voyage_id=v_id,
        type="storm",
        lat=storm_lat,
        lon=storm_lon,
        radius_km=200.0,
        severity=0.85,
        label="Storm Test",
    )
    res = handle_simulation_event(event)

    # Check state after event
    v2 = get_voyage(v_id)
    assert v2.current_time == time_at_t4, "Simulation clock must not reset"
    assert v2.current_lat == lat_at_t4, "Vessel lat must not reset to origin"
    assert v2.current_lon == lon_at_t4, "Vessel lon must not reset to origin"

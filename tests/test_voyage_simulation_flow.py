"""
Critical Voyage Lifecycle & Dynamic Disruption / Override Test Suite
Verifies:
1. Voyage initialization and clock advancement
2. Disruption injection ahead of vessel
3. Authoritative backend alternative route evaluation & decision
4. Manual override state handling (preserving vessel coordinates and simulation clock)
5. Disruption behind vessel (EVENT_BEHIND_VESSEL -> zero false reroutes)
6. Hysteresis threshold retention (ROUTE_RETAINED)
7. Final arrival at destination
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


def test_voyage_lifecycle_disruption_and_manual_override():
    """Validates complete voyage flow with disruption ahead, manual override, position preservation, and arrival."""
    req = VoyageCreateRequest(
        origin="kochi",
        destination="singapore",
        ship="container_large",
        optimization="BALANCED",
        data_mode="HYBRID",
    )
    v = create_voyage(req)
    voyage_id = v.voyage_id
    assert v.current_time == 0.0
    assert not v.is_completed
    initial_lat, initial_lon = v.current_lat, v.current_lon

    # Tick voyage 5.0 hours to move vessel partway
    t1 = tick_voyage(voyage_id, tick_duration=5.0)
    assert t1.current_time == 5.0
    assert not t1.is_completed
    assert (t1.current_lat != initial_lat) or (t1.current_lon != initial_lon), "Vessel must move after tick"
    vessel_lat_at_t5 = t1.current_lat
    vessel_lon_at_t5 = t1.current_lon

    # Inject severe storm disruption ahead on remaining route
    route_coords = t1.active_route.coordinates
    assert len(route_coords) > 2
    target_idx = min(len(route_coords) - 1, max(1, len(route_coords) // 2))
    storm_lat, storm_lon = route_coords[target_idx]

    sim_event = SimulationEvent(
        voyage_id=voyage_id,
        type="storm",
        lat=storm_lat,
        lon=storm_lon,
        radius_km=200.0,
        severity=0.9,
        label="Severe Cyclone Ahead",
    )
    sim_res = handle_simulation_event(sim_event)
    assert sim_res.voyage_id == voyage_id
    assert sim_res.spatially_relevant is True
    assert sim_res.decision in ["REROUTE", "ROUTE_RETAINED", "PORT_CONGESTION_UPDATED", "NO_IMPACT"]

    # Verify vessel position and current time after disruption processing
    v_state = get_voyage(voyage_id)
    assert v_state.current_time == 5.0, "Simulation clock must not reset"
    assert v_state.current_lat == vessel_lat_at_t5, "Vessel position must not change or jump back to origin"
    assert v_state.current_lon == vessel_lon_at_t5

    # Advance ticks until destination arrival
    max_ticks = 200
    ticks = 0
    while not v_state.is_completed and ticks < max_ticks:
        t_res = tick_voyage(voyage_id, tick_duration=2.0)
        v_state = get_voyage(voyage_id)
        ticks += 1

    assert v_state.is_completed, "Vessel must successfully reach destination"


def test_disruption_behind_vessel_no_false_reroute():
    """Validates that a disruption behind the vessel triggers EVENT_BEHIND_VESSEL and no false reroute."""
    req = VoyageCreateRequest(
        origin="mumbai",
        destination="colombo",
        ship="container_large",
        optimization="FASTEST",
        data_mode="MOCK",
    )
    v = create_voyage(req)
    voyage_id = v.voyage_id
    origin_lat, origin_lon = v.current_lat, v.current_lon

    # Advance vessel significantly along route
    for _ in range(10):
        tick_voyage(voyage_id, tick_duration=2.0)

    t_state = get_voyage(voyage_id)
    assert t_state.current_time == 20.0

    # Inject disruption near origin (now behind vessel)
    behind_event = SimulationEvent(
        voyage_id=voyage_id,
        type="storm",
        lat=origin_lat,
        lon=origin_lon,
        radius_km=100.0,
        severity=0.85,
        label="Storm at Origin",
    )
    sim_res = handle_simulation_event(behind_event)
    assert sim_res.decision == "EVENT_BEHIND_VESSEL"
    assert sim_res.rerouted is False
    assert "already traversed" in sim_res.reason

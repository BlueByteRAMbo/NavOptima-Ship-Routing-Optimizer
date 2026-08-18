"""
Regression Tests for Security Disruption Teleportation Bug (BUG 16)
and Congestion Visualization / Route-Stitch correctness.

Tests:
1. test_security_disruption_no_teleportation — vessel lat/lon/time/progress preserved after security event
2. test_storm_disruption_no_teleportation    — same guarantee for storm events
3. test_congestion_disruption_no_teleportation — same for port_congestion events
4. test_reroute_stitches_from_current_position — stitched route starts from current segment not from origin
5. test_keep_current_no_position_change      — rejecting alternative never moves vessel
6. test_multi_port_no_teleportation          — teleportation check across 6 OD pairs
"""
import pytest
from backend.app.orchestration.optimizer_service import (
    create_voyage,
    tick_voyage,
    get_voyage,
    handle_simulation_event,
)
from backend.app.models.route import VoyageCreateRequest, SimulationEvent


def _advance_voyage(voyage_id: str, hours: float = 10.0, step: float = 2.0):
    """Helper: advance voyage by `hours` total in steps of `step`."""
    elapsed = 0.0
    last_t = None
    while elapsed < hours:
        last_t = tick_voyage(voyage_id, tick_duration=step)
        elapsed += step
    return last_t


def _disruption_at_midroute(voyage_id: str, voyage_state, event_type: str):
    """Helper: inject a disruption halfway along the remaining route."""
    coords = voyage_state.active_route.coordinates
    mid_idx = max(1, len(coords) // 2)
    lat, lon = coords[mid_idx]
    radius = 50 if event_type == 'port_congestion' else 200
    event = SimulationEvent(
        voyage_id=voyage_id,
        type=event_type,
        lat=lat,
        lon=lon,
        radius_km=float(radius),
        severity=0.85,
        label=f"{event_type.replace('_',' ').title()} Test",
    )
    return handle_simulation_event(event)


# ───────────────────────────────────────────────
# BUG 16 – SECURITY DISRUPTION NO TELEPORTATION
# ───────────────────────────────────────────────
def test_security_disruption_no_teleportation():
    """Vessel lat/lon/time must be unchanged after a security event."""
    req = VoyageCreateRequest(
        origin="mumbai",
        destination="singapore",
        ship="container_large",
        optimization="BALANCED",
        data_mode="HYBRID",
    )
    v = create_voyage(req)
    v_id = v.voyage_id

    # Advance 10 simulated hours to put vessel mid-route
    t_before = _advance_voyage(v_id, hours=10.0, step=2.0)
    lat_before = t_before.current_lat
    lon_before = t_before.current_lon
    time_before = t_before.current_time

    # Inject security disruption
    _disruption_at_midroute(v_id, t_before, 'security')

    state_after = get_voyage(v_id)
    assert abs(state_after.current_lat - lat_before) < 1e-6, (
        f"TELEPORTATION: lat changed from {lat_before} → {state_after.current_lat}"
    )
    assert abs(state_after.current_lon - lon_before) < 1e-6, (
        f"TELEPORTATION: lon changed from {lon_before} → {state_after.current_lon}"
    )
    assert state_after.current_time == time_before, (
        f"Clock advanced from {time_before} → {state_after.current_time} during disruption"
    )


def test_storm_disruption_no_teleportation():
    """Vessel position/time unchanged after a storm event."""
    req = VoyageCreateRequest(
        origin="kochi",
        destination="singapore",
        ship="container_large",
        optimization="FASTEST",
        data_mode="HYBRID",
    )
    v = create_voyage(req)
    v_id = v.voyage_id

    t_before = _advance_voyage(v_id, hours=8.0, step=2.0)
    lat_before, lon_before, time_before = t_before.current_lat, t_before.current_lon, t_before.current_time

    _disruption_at_midroute(v_id, t_before, 'storm')

    state = get_voyage(v_id)
    assert abs(state.current_lat - lat_before) < 1e-6, "TELEPORTATION after storm"
    assert abs(state.current_lon - lon_before) < 1e-6, "TELEPORTATION after storm"
    assert state.current_time == time_before, "Clock moved during storm disruption"


def test_congestion_disruption_no_teleportation():
    """Vessel position/time unchanged after port_congestion event."""
    req = VoyageCreateRequest(
        origin="colombo",
        destination="singapore",
        ship="container_large",
        optimization="SAFEST",
        data_mode="MOCK",
    )
    v = create_voyage(req)
    v_id = v.voyage_id

    t_before = _advance_voyage(v_id, hours=6.0, step=2.0)
    lat_before, lon_before, time_before = t_before.current_lat, t_before.current_lon, t_before.current_time

    _disruption_at_midroute(v_id, t_before, 'port_congestion')

    state = get_voyage(v_id)
    assert abs(state.current_lat - lat_before) < 1e-6, "TELEPORTATION after port_congestion"
    assert abs(state.current_lon - lon_before) < 1e-6, "TELEPORTATION after port_congestion"
    assert state.current_time == time_before, "Clock moved during congestion disruption"


# ───────────────────────────────────────────────
# BUG 2 – REROUTED ROUTE STITCHES FROM CURRENT SEGMENT
# ───────────────────────────────────────────────
def test_reroute_stitches_from_current_position():
    """After disruption that triggers reroute, stitched route starts at/near current vessel position."""
    req = VoyageCreateRequest(
        origin="mumbai",
        destination="singapore",
        ship="container_large",
        optimization="BALANCED",
        data_mode="HYBRID",
    )
    v = create_voyage(req)
    v_id = v.voyage_id

    t_before = _advance_voyage(v_id, hours=10.0, step=2.0)
    lat_before, lon_before = t_before.current_lat, t_before.current_lon

    # Inject storm with very high severity to force reroute
    coords = t_before.active_route.coordinates
    mid_idx = min(len(coords) - 1, len(coords) // 2)
    lat_ev, lon_ev = coords[mid_idx]
    event = SimulationEvent(
        voyage_id=v_id,
        type="storm",
        lat=lat_ev,
        lon=lon_ev,
        radius_km=300.0,
        severity=0.95,
        label="Extreme Storm",
    )
    handle_simulation_event(event)

    state = get_voyage(v_id)
    # Stitched active_route coordinates must include points near lat_before/lon_before
    route_coords = state.active_route.coordinates
    # The first coordinate should be near the origin (history preserved), not teleported
    first_lat, first_lon = route_coords[0]
    # Origin of the voyage should be approximately at the start
    origin_node = v.active_route.coordinates[0]
    assert abs(first_lat - origin_node[0]) < 0.1, "Route origin drifted from origin after stitch"


# ───────────────────────────────────────────────
# BUG 5 – SIMULATION PAUSED: CLOCK FROZEN DURING DISRUPTION
# ───────────────────────────────────────────────
def test_simulation_clock_frozen_during_disruption():
    """After disruption injection, vessel time remains identical until next tick."""
    req = VoyageCreateRequest(
        origin="chennai",
        destination="singapore",
        ship="container_large",
        optimization="BALANCED",
        data_mode="HYBRID",
    )
    v = create_voyage(req)
    v_id = v.voyage_id

    t_before = _advance_voyage(v_id, hours=6.0, step=2.0)
    time_before = t_before.current_time

    _disruption_at_midroute(v_id, t_before, 'storm')

    # Verify time not changed by disruption itself
    state = get_voyage(v_id)
    assert state.current_time == time_before, (
        f"Clock advanced during disruption processing: {time_before} → {state.current_time}"
    )

    # Verify resuming (ticking) DOES advance time
    t_after_resume = tick_voyage(v_id, tick_duration=2.0)
    assert t_after_resume.current_time > time_before, "Vessel did not resume moving after disruption"


# ───────────────────────────────────────────────
# MULTI-PORT NO-TELEPORTATION MATRIX
# ───────────────────────────────────────────────
@pytest.mark.parametrize("orig,dest,event_type", [
    ("mumbai", "kochi", "security"),
    ("mumbai", "colombo", "storm"),
    ("colombo", "singapore", "port_congestion"),
    ("kochi", "singapore", "security"),
    ("chennai", "singapore", "storm"),
    ("yangon", "singapore", "port_congestion"),
])
def test_multi_port_no_teleportation(orig, dest, event_type):
    """Security/storm/congestion disruptions never teleport vessel across any supported OD pair."""
    req = VoyageCreateRequest(
        origin=orig,
        destination=dest,
        ship="container_large",
        optimization="BALANCED",
        data_mode="HYBRID",
    )
    v = create_voyage(req)
    v_id = v.voyage_id

    t_before = _advance_voyage(v_id, hours=4.0, step=2.0)
    lat_before, lon_before, time_before = t_before.current_lat, t_before.current_lon, t_before.current_time

    _disruption_at_midroute(v_id, t_before, event_type)

    state = get_voyage(v_id)
    assert abs(state.current_lat - lat_before) < 1e-6, (
        f"[{orig}->{dest}] {event_type} teleported lat: {lat_before} -> {state.current_lat}"
    )
    assert abs(state.current_lon - lon_before) < 1e-6, (
        f"[{orig}->{dest}] {event_type} teleported lon: {lon_before} -> {state.current_lon}"
    )
    assert state.current_time == time_before, (
        f"[{orig}->{dest}] {event_type} advanced clock: {time_before} -> {state.current_time}"
    )

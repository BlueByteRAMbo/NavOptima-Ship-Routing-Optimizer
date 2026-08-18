"""
Test Stateful Voyage Lifecycle & Dynamic Rerouting Tick
"""
import os
import sys
import pytest

from backend.app.orchestration.optimizer_service import (
    create_voyage,
    get_voyage,
    tick_voyage,
)
from backend.app.models.route import VoyageCreateRequest


def test_stateful_voyage_lifecycle():
    # 1. Create voyage
    req = VoyageCreateRequest(
        origin="mumbai",
        destination="singapore",
        ship="container",
        optimization="BALANCED",
        data_mode="HYBRID",
        hysteresis_threshold=0.05,
    )
    init_res = create_voyage(req)
    assert init_res.voyage_id is not None
    assert init_res.current_node_id == "Mumbai"
    assert not init_res.is_completed
    assert len(init_res.active_route.coordinates) > 0

    # 2. Get voyage
    state_res = get_voyage(init_res.voyage_id)
    assert state_res.voyage_id == init_res.voyage_id

    # 3. Tick voyage clock
    tick_res = tick_voyage(init_res.voyage_id, tick_duration=2.0)
    assert tick_res.current_time == 2.0
    assert tick_res.voyage_id == init_res.voyage_id


def test_voyage_storm_reroute_tick():
    # Voyage with storm overlay intersecting route
    req = VoyageCreateRequest(
        origin="mumbai",
        destination="colombo",
        ship="container",
        optimization="BALANCED",
        data_mode="HYBRID",
        hysteresis_threshold=0.05,
        storm={
            "start_lat": 12.0,
            "start_lon": 75.0,
            "speed_knots": 0.0,
            "direction_deg": 90.0,
            "radius_nm": 150.0,
            "intensity_max": 9.0,
        },
    )
    voyage_state = create_voyage(req)
    assert voyage_state.voyage_id is not None

    # Advance time through multiple ticks
    tick1 = tick_voyage(voyage_state.voyage_id, tick_duration=5.0)
    assert tick1.current_time == 5.0

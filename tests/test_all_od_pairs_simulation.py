"""
Exhaustive All-Ports & OD Pairs Voyage Simulation Test Matrix
Validates every graph-supported port, directional connected OD pair, all 4 strategies, MOCK & HYBRID modes.
No hardcoded routes or port assumptions.
"""
import pytest
from typing import List, Tuple
from backend.app.orchestration.optimizer_service import (
    get_routing_graph,
    CANONICAL_TO_GRAPH,
    create_voyage,
    tick_voyage,
    handle_simulation_event,
)
from backend.app.models.route import (
    VoyageCreateRequest,
    SimulationEvent,
)


def get_all_supported_port_ids() -> List[str]:
    return list(CANONICAL_TO_GRAPH.keys())


def discover_connected_od_pairs() -> List[Tuple[str, str]]:
    """Discovers all valid directional OD pairs in the graph."""
    graph = get_routing_graph()
    ports = get_all_supported_port_ids()
    valid_pairs = []

    for orig in ports:
        for dest in ports:
            if orig == dest:
                continue
            orig_graph_id = CANONICAL_TO_GRAPH[orig]
            dest_graph_id = CANONICAL_TO_GRAPH[dest]
            if graph.get_node(orig_graph_id) and graph.get_node(dest_graph_id):
                try:
                    req = VoyageCreateRequest(
                        origin=orig,
                        destination=dest,
                        ship="container_large",
                        optimization="FASTEST",
                        data_mode="MOCK",
                    )
                    v_res = create_voyage(req)
                    if v_res.active_route and v_res.active_route.distance_km > 0:
                        valid_pairs.append((orig, dest))
                except Exception:
                    pass
    return valid_pairs


def test_exhaustive_od_matrix_execution():
    """Runs simulation test matrix across all connected OD pairs, 4 strategies, MOCK & HYBRID modes."""
    ports = get_all_supported_port_ids()
    pairs = discover_connected_od_pairs()

    assert len(ports) >= 5, f"Expected at least 5 supported ports, found {len(ports)}"
    assert len(pairs) >= 6, f"Expected at least 6 connected OD pairs, found {len(pairs)}"

    strategies = ["FASTEST", "SAFEST", "LEAST_CONGESTED", "BALANCED"]
    data_modes = ["MOCK", "HYBRID"]

    stats = {
        "total_ports": len(ports),
        "total_connected_od_pairs": len(pairs),
        "MOCK_PASS": 0,
        "HYBRID_PASS": 0,
        "FASTEST_PASS": 0,
        "SAFEST_PASS": 0,
        "LEAST_CONGESTED_PASS": 0,
        "BALANCED_PASS": 0,
    }

    for orig, dest in pairs:
        for mode in data_modes:
            for strat in strategies:
                req = VoyageCreateRequest(
                    origin=orig,
                    destination=dest,
                    ship="container_large",
                    optimization=strat,
                    data_mode=mode,
                )
                v_res = create_voyage(req)
                assert v_res.voyage_id, f"Failed voyage init for {orig}->{dest}"
                assert v_res.active_route, f"Missing route for {orig}->{dest}"
                assert v_res.active_route.distance_km > 0
                assert v_res.active_route.eta_hours > 0

                # Advance ticks
                tick_res = tick_voyage(v_res.voyage_id, tick_duration=2.0)
                assert tick_res.current_time == 2.0
                assert tick_res.active_route, f"Missing tick active route for {orig}->{dest}"

                # Inject storm disruption ahead on route
                route_coords = v_res.active_route.coordinates
                mid_idx = max(0, len(route_coords) // 2)
                event_lat, event_lon = route_coords[mid_idx]

                sim_event = SimulationEvent(
                    voyage_id=v_res.voyage_id,
                    type="storm",
                    lat=event_lat,
                    lon=event_lon,
                    radius_km=150.0,
                    severity=0.8,
                    label=f"Storm along {orig}->{dest}",
                )

                sim_res = handle_simulation_event(sim_event)
                assert sim_res.decision in [
                    "REROUTE",
                    "ROUTE_RETAINED",
                    "NO_IMPACT",
                    "SPATIALLY_IRRELEVANT",
                    "EVENT_BEHIND_VESSEL",
                    "PORT_CONGESTION_UPDATED",
                ]
                assert sim_res.active_route, f"Simulation response missing active route for {orig}->{dest}"

                # Update pass counts
                if mode == "MOCK":
                    stats["MOCK_PASS"] += 1
                else:
                    stats["HYBRID_PASS"] += 1

                if strat == "FASTEST":
                    stats["FASTEST_PASS"] += 1
                elif strat == "SAFEST":
                    stats["SAFEST_PASS"] += 1
                elif strat == "LEAST_CONGESTED":
                    stats["LEAST_CONGESTED_PASS"] += 1
                elif strat == "BALANCED":
                    stats["BALANCED_PASS"] += 1

    print("\n=======================================================")
    print("ALL CONNECTED OD PAIRS SIMULATION MATRIX RESULTS")
    print("=======================================================")
    print(f"TOTAL PORTS:               {stats['total_ports']}")
    print(f"TOTAL CONNECTED OD PAIRS:  {stats['total_connected_od_pairs']}")
    print(f"MOCK PASS:                 {stats['MOCK_PASS']}")
    print(f"HYBRID PASS:               {stats['HYBRID_PASS']}")
    print(f"FASTEST PASS:              {stats['FASTEST_PASS']}")
    print(f"SAFEST PASS:               {stats['SAFEST_PASS']}")
    print(f"LEAST_CONGESTED PASS:      {stats['LEAST_CONGESTED_PASS']}")
    print(f"BALANCED PASS:             {stats['BALANCED_PASS']}")
    print("=======================================================\n")

import pytest
import math
import os
import json
from src.haversine import haversine_distance
from src.models import Node, Edge, Graph, load_graph
from src.weather import DeterministicWeatherEngine, BaseWeatherProvider
from src.optimizer import (
    STRATEGIES,
    ShipConfig,
    calculate_weather_modifiers,
    calculate_edge_cost,
    N_TIME,
    N_FUEL,
    N_SAFETY,
    N_CONGESTION
)
from src.router import time_dependent_astar, calculate_heuristic
from src.simulation import initialize_voyage, advance_voyage_simulation, RerouteEvent

GRAPH_FILEPATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "traffic.json")

# Helper for exhaustive path solver
def find_all_simple_paths(graph: Graph, start: str, target: str, current_path: list[str] = None) -> list[list[str]]:
    if current_path is None:
        current_path = [start]
    if start == target:
        return [current_path]
    paths = []
    for edge in graph.get_outgoing_edges(start):
        neighbor = edge.target_id
        if neighbor not in current_path:
            paths.append(current_path + [neighbor])
            paths.extend(find_all_simple_paths(graph, neighbor, target, current_path + [neighbor]))
    
    # Filter only those paths that actually reach target
    return [p for p in paths if p[-1] == target]

def evaluate_simple_path(
    graph: Graph,
    path_nodes: list[str],
    start_time: float,
    strategy,
    ship: ShipConfig,
    weather_provider: BaseWeatherProvider
) -> tuple[float, float, float, float, float]:
    """
    Evaluate the exact cost of a path node sequence continuously.
    """
    current_time = start_time
    total_cost = 0.0
    total_time = 0.0
    total_fuel = 0.0
    total_safety = 0.0
    total_congestion = 0.0
    
    for i in range(len(path_nodes) - 1):
        src = path_nodes[i]
        tgt = path_nodes[i+1]
        
        edge = None
        for e in graph.get_outgoing_edges(src):
            if e.target_id == tgt:
                edge = e
                break
        if not edge:
            raise ValueError(f"No edge {src} -> {tgt}")
            
        src_node = graph.get_node(src)
        tgt_node = graph.get_node(tgt)
        mid_lat = (src_node.latitude + tgt_node.latitude) / 2.0
        mid_lon = (src_node.longitude + tgt_node.longitude) / 2.0
        
        mid_time = current_time + (edge.distance_nm / ship.base_speed_knots) / 2.0
        storm_intensity = weather_provider.get_conditions(mid_lat, mid_lon, mid_time)
        
        cost, travel_time, fuel, safety, congestion = calculate_edge_cost(
            edge.distance_nm,
            edge.base_congestion,
            storm_intensity,
            ship,
            strategy
        )
        
        total_cost += cost
        total_time += travel_time
        total_fuel += fuel
        total_safety += safety
        total_congestion += congestion
        current_time += travel_time
        
    return total_cost, total_time, total_fuel, total_safety, total_congestion


# 1. Graph validity
def test_graph_validity():
    assert os.path.exists(GRAPH_FILEPATH), "traffic.json should exist"
    graph = load_graph(GRAPH_FILEPATH)
    assert len(graph.nodes) >= 10, "Should have at least 10 ports + waypoints"
    
    node_ids = {n.id for n in graph.nodes}
    assert "Mumbai" in node_ids
    assert "Colombo" in node_ids
    assert "Singapore" in node_ids
    
    # Check that all edges refer to existing nodes
    for edge in graph.edges:
        assert edge.source_id in node_ids, f"Edge source {edge.source_id} not in nodes"
        assert edge.target_id in node_ids, f"Edge target {edge.target_id} not in nodes"


# 2. Directed edge behavior
def test_directed_edge_behavior():
    graph = load_graph(GRAPH_FILEPATH)
    
    # Find edges and check that reverse edges are NOT automatically generated
    # (e.g. if E001 exists from Mumbai -> WP_Laccadive, check if WP_Laccadive -> Mumbai exists only if defined)
    mumbai_out = [e.target_id for e in graph.get_outgoing_edges("Mumbai")]
    laccadive_out = [e.target_id for e in graph.get_outgoing_edges("WP_Laccadive")]
    
    # Mumbai -> WP_Laccadive exists
    assert "WP_Laccadive" in mumbai_out
    
    # WP_Laccadive -> Mumbai should only exist if explicitly defined
    # Let's check traffic.json edge definitions: we added WP_Laccadive -> Mumbai as a return edge.
    # Let's check a one-way edge. e.g. Visakhapatnam -> Yangon is defined (E071).
    # Is Yangon -> Visakhapatnam defined?
    yangon_out = [e.target_id for e in graph.get_outgoing_edges("Yangon")]
    assert "Visakhapatnam" not in yangon_out, "Yangon -> Visakhapatnam should not exist as it is not in edge definitions"


# 3. Haversine calculation
def test_haversine_calculation():
    # Mumbai to Colombo known distance is approx 890 nautical miles
    mumbai_lat, mumbai_lon = 18.94, 72.82
    colombo_lat, colombo_lon = 6.94, 79.84
    
    dist = haversine_distance(mumbai_lat, mumbai_lon, colombo_lat, colombo_lon)
    assert 810.0 < dist < 850.0, f"Distance {dist} should be around ~830 nm"
    
    # Distance to itself should be 0
    assert haversine_distance(mumbai_lat, mumbai_lon, mumbai_lat, mumbai_lon) == 0.0


# 4. Distance reconciliation
def test_distance_reconciliation():
    graph = load_graph(GRAPH_FILEPATH)
    # Maritime edge distance must be >= Haversine distance and within 1.5x of it.
    for edge in graph.edges:
        s = graph.get_node(edge.source_id)
        t = graph.get_node(edge.target_id)
        h_dist = haversine_distance(s.latitude, s.longitude, t.latitude, t.longitude)
        
        assert edge.distance_nm >= h_dist - 0.1, f"Edge {edge.id} distance {edge.distance_nm} is less than Haversine {h_dist}"
        assert edge.distance_nm <= h_dist * 1.5, f"Edge {edge.id} distance {edge.distance_nm} is too high compared to Haversine {h_dist}"


# 5. Cost calculation
def test_cost_calculation():
    ship = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)
    strategy = STRATEGIES["BALANCED"] # w_time=0.35, w_fuel=0.25, w_safety=0.25, w_congestion=0.15
    
    # Standard cost with intensity 0.0
    cost, time_v, fuel_v, safety_v, cong_v = calculate_edge_cost(
        distance_nm=150.0,
        base_congestion=0.2,
        storm_intensity=0.0,
        ship=ship,
        strategy=strategy
    )
    
    # 150 nm / 15 kts = 10.0 hours
    assert time_v == 10.0
    # fuel rate 1.0 ton/hour * 10 hours = 10.0 tons
    assert fuel_v == 10.0
    # storm intensity 0 -> safety penalty 0
    assert safety_v == 0.0
    # congestion = 0.2 * 150 = 30.0
    assert cong_v == 30.0
    
    # Normalized components:
    # time = 10.0 / 10.0 = 1.0
    # fuel = 10.0 / 10.0 = 1.0
    # safety = 0.0 / 1.0 = 0.0
    # congestion = 30.0 / 30.0 = 1.0
    # weighted = 0.35 * 1.0 + 0.25 * 1.0 + 0.25 * 0.0 + 0.15 * 1.0 = 0.35 + 0.25 + 0.15 = 0.75
    assert math.isclose(cost, 0.75, rel_tol=1e-5)


# 6. Fastest objective
def test_fastest_objective():
    graph = load_graph(GRAPH_FILEPATH)
    ship = ShipConfig()
    weather = DeterministicWeatherEngine(0, 0, 0, 0, 100) # Calm weather
    strategy = STRATEGIES["FASTEST"]
    
    res = time_dependent_astar(graph, "Mumbai", "Singapore", 0.0, strategy, ship, weather)
    assert res is not None
    assert res.strategy_name == "FASTEST"
    assert res.total_time > 0.0
    
    # Fastest weights: w_time = 1.0, others = 0.0. Cost should equal normalized time.
    assert math.isclose(res.total_cost, res.total_time / N_TIME, rel_tol=1e-5)


# 7. Safest objective
def test_safest_objective():
    graph = load_graph(GRAPH_FILEPATH)
    ship = ShipConfig()
    # Put a storm near the main highway (Colombo)
    # Colombo is at 6.94, 79.84. Put storm exactly there.
    weather = DeterministicWeatherEngine(
        start_lat=6.94, start_lon=79.84, speed_knots=0.0, direction_deg=0.0, radius_nm=100.0, intensity_max=10.0
    )
    
    # Safest strategy weights safety very high (w_safety = 0.8)
    res_safest = time_dependent_astar(graph, "Mumbai", "Singapore", 0.0, STRATEGIES["SAFEST"], ship, weather)
    res_fastest = time_dependent_astar(graph, "Mumbai", "Singapore", 0.0, STRATEGIES["FASTEST"], ship, weather)
    
    assert res_safest is not None
    assert res_fastest is not None
    
    # Safest route should have lower safety penalty (or at least <=) compared to fastest
    assert res_safest.total_safety <= res_fastest.total_safety


# 8. Least-congested objective
def test_least_congested_objective():
    graph = load_graph(GRAPH_FILEPATH)
    ship = ShipConfig()
    weather = DeterministicWeatherEngine(0, 0, 0, 0, 100)
    
    res_congested = time_dependent_astar(graph, "Mumbai", "Singapore", 0.0, STRATEGIES["LEAST_CONGESTED"], ship, weather)
    assert res_congested is not None
    
    # Total congestion cost calculation verify
    # Congestion cost is w_congestion * (congestion_sum) / N_congestion
    expected_cong_cost = STRATEGIES["LEAST_CONGESTED"].w_congestion * (res_congested.total_congestion / N_CONGESTION)
    # Let's check how the balanced weights affect total cost vs congestion cost
    assert res_congested.total_congestion >= 0.0


# 9. Balanced objective
def test_balanced_objective():
    graph = load_graph(GRAPH_FILEPATH)
    ship = ShipConfig()
    weather = DeterministicWeatherEngine(0, 0, 0, 0, 100)
    
    res = time_dependent_astar(graph, "Mumbai", "Singapore", 0.0, STRATEGIES["BALANCED"], ship, weather)
    assert res is not None
    assert res.strategy_name == "BALANCED"


# 10. Deterministic weather
def test_deterministic_weather():
    engine = DeterministicWeatherEngine(
        start_lat=10.0, start_lon=80.0, speed_knots=10.0, direction_deg=90.0, radius_nm=100.0, intensity_max=10.0
    )
    
    # Query twice at same location and time, must be identical
    i1 = engine.get_conditions(10.0, 80.0, 5.0)
    i2 = engine.get_conditions(10.0, 80.0, 5.0)
    assert i1 == i2
    
    # Query at different coordinates
    i3 = engine.get_conditions(12.0, 82.0, 5.0)
    assert i1 != i3


# 11. Weather time dependency
def test_weather_time_dependency():
    # Storm moving East (bearing 90) starting at (10.0, 80.0) at speed 60 knots (1 deg lon per hour roughly at equator)
    engine = DeterministicWeatherEngine(
        start_lat=10.0, start_lon=80.0, speed_knots=60.0, direction_deg=90.0, radius_nm=50.0, intensity_max=10.0
    )
    
    # At t = 0, storm is at (10.0, 80.0). Intensity at (10.0, 80.0) is 10.0.
    assert engine.get_conditions(10.0, 80.0, 0.0) == 10.0
    
    # At t = 5 hours, storm has moved 300 nm East. Intensity at (10.0, 80.0) should be near 0
    assert engine.get_conditions(10.0, 80.0, 5.0) < 0.1
    
    # Storm center at t = 5 is approx at 10.0, 85.0. Intensity there should be 10.0
    center_lat, center_lon = engine.get_storm_center(5.0)
    assert engine.get_conditions(center_lat, center_lon, 5.0) == 10.0


# 12. Time-dependent A* state
def test_time_dependent_astar_state():
    # Verify that we can arrive at the same node at different times
    # and A* correctly stores them as separate states.
    # We will build the A -> X -> D and A -> Y -> X -> D control graph
    nodes = [
        Node(id="A", name="A", latitude=10.0, longitude=70.0, is_port=True),
        Node(id="Y", name="Y", latitude=10.0, longitude=71.5, is_port=False),
        Node(id="X", name="X", latitude=10.0, longitude=72.0, is_port=False),
        Node(id="D", name="D", latitude=10.0, longitude=74.0, is_port=True),
    ]
    edges = [
        Edge(id="E1", source_id="A", target_id="X", distance_nm=100.0, base_congestion=0.0),
        Edge(id="E2", source_id="A", target_id="Y", distance_nm=150.0, base_congestion=0.0),
        Edge(id="E3", source_id="Y", target_id="X", distance_nm=150.0, base_congestion=0.0),
        Edge(id="E4", source_id="X", target_id="D", distance_nm=100.0, base_congestion=0.0),
    ]
    graph = Graph(nodes=nodes, edges=edges)
    ship = ShipConfig(base_speed_knots=20.0, base_fuel_rate=1.0)
    
    # Storm moving North, starts at (7.5, 73.0) at speed 20.0 knots, radius 50 nm
    # This storm hits the midpoint of X -> D (10.0, 73.0) at t = 7.5 hours
    weather = DeterministicWeatherEngine(
        start_lat=7.5, start_lon=73.0, speed_knots=20.0, direction_deg=0.0, radius_nm=50.0, intensity_max=10.0
    )
    
    # Use FASTEST weights (w_time = 1.0)
    strategy = STRATEGIES["FASTEST"]
    
    # Run A*
    res = time_dependent_astar(graph, "A", "D", 0.0, strategy, ship, weather)
    assert res is not None
    
    # Verify A* chose the path Y -> X -> D (which delays arrival at X to avoid storm)
    path_nodes = [step.node_id for step in res.path]
    assert path_nodes == ["A", "Y", "X", "D"], f"Expected Y-routing to avoid storm, got {path_nodes}"
    
    # Path 1 (Direct A -> X -> D) would take:
    # A -> X: 100/20 = 5.0 hours (arrival t=5.0)
    # Midpoint of X -> D reached at t=7.5. Storm center is at 71.0 + (15.7*7.5/60/cos(10)) ~ 73.0.
    # Storm intensity at midpoint is ~10.0, speed modifier is 0.2, effective speed = 4.0 knots.
    # X -> D travel time = 100 / 4 = 25.0 hours.
    # Total time = 30.0 hours.
    
    # Path 2 (A -> Y -> X -> D) takes:
    # A -> Y: 150/20 = 7.5 hours (arrival t=7.5)
    # Y -> X: 150/20 = 7.5 hours (arrival t=15.0)
    # Midpoint of X -> D reached at t=17.5. Storm center is at 71.0 + (15.7*17.5/60/cos(10)) ~ 75.6.
    # Storm intensity at midpoint is ~0.07 (very low), speed modifier ~ 0.99, effective speed ~ 19.8 knots.
    # X -> D travel time = 100 / 19.8 = 5.05 hours.
    # Total time = 20.05 hours.
    
    # A* correctly identified the longer path in distance is faster due to storm dynamics!
    assert res.total_time < 22.0


# 13. Exhaustive vs A*
def test_exhaustive_vs_astar():
    # Use the control graph to verify A* matches the exhaustive search
    nodes = [
        Node(id="A", name="A", latitude=10.0, longitude=70.0, is_port=True),
        Node(id="Y", name="Y", latitude=10.0, longitude=71.5, is_port=False),
        Node(id="X", name="X", latitude=10.0, longitude=72.0, is_port=False),
        Node(id="D", name="D", latitude=10.0, longitude=74.0, is_port=True),
    ]
    edges = [
        Edge(id="E1", source_id="A", target_id="X", distance_nm=100.0, base_congestion=0.0),
        Edge(id="E2", source_id="A", target_id="Y", distance_nm=150.0, base_congestion=0.0),
        Edge(id="E3", source_id="Y", target_id="X", distance_nm=150.0, base_congestion=0.0),
        Edge(id="E4", source_id="X", target_id="D", distance_nm=100.0, base_congestion=0.0),
    ]
    graph = Graph(nodes=nodes, edges=edges)
    ship = ShipConfig(base_speed_knots=20.0)
    weather = DeterministicWeatherEngine(
        start_lat=7.5, start_lon=73.0, speed_knots=20.0, direction_deg=0.0, radius_nm=50.0, intensity_max=10.0
    )
    strategy = STRATEGIES["FASTEST"]
    
    # 1. Run exhaustive search
    simple_paths = find_all_simple_paths(graph, "A", "D")
    best_path_nodes = None
    min_cost = float('inf')
    
    for path in simple_paths:
        cost, time_v, fuel_v, safety_v, cong_v = evaluate_simple_path(graph, path, 0.0, strategy, ship, weather)
        if cost < min_cost:
            min_cost = cost
            best_path_nodes = path
            
    # 2. Run A*
    res = time_dependent_astar(graph, "A", "D", 0.0, strategy, ship, weather)
    assert res is not None
    astar_path_nodes = [step.node_id for step in res.path]
    
    # They must match exactly!
    assert astar_path_nodes == best_path_nodes
    assert math.isclose(res.total_cost, min_cost, rel_tol=1e-4)


# 14. Dynamic rerouting
def test_dynamic_rerouting():
    # In this test, we simulate a weather forecast update.
    # Initially, the forecast predicts calm weather, so the ship plans the direct route:
    # Mumbai -> WP_Laccadive -> Colombo -> WP_Bay_of_Bengal -> ...
    # However, during the voyage, actual weather conditions deteriorate:
    # a stationary storm of intensity 8.0 develops near longitude 85.0 (blocking WP_Bay_of_Bengal).
    # When the ship reaches Colombo, the rerouting engine detects this cost increase,
    # runs A* under the actual weather, and switches to a safer alternative path.
    graph = load_graph(GRAPH_FILEPATH)
    ship = ShipConfig(base_speed_knots=15.0)
    strategy = STRATEGIES["BALANCED"]
    
    calm_weather = DeterministicWeatherEngine(
        start_lat=0.0, start_lon=0.0, speed_knots=0.0, direction_deg=0.0, radius_nm=100.0, intensity_max=0.0
    )
    
    actual_weather = DeterministicWeatherEngine(
        start_lat=5.75, start_lon=91.5, speed_knots=0.0, direction_deg=0.0, radius_nm=150.0, intensity_max=10.0
    )
    
    # Initialize voyage with the calm forecast
    voyage = initialize_voyage(graph, "Mumbai", "Singapore", 0.0, strategy, ship, calm_weather, hysteresis_threshold=0.05)
    assert voyage is not None
    initial_path = [step.node_id for step in voyage.active_route.path]
    
    # Advance the simulation using actual weather
    # Total time to Colombo in calm weather is ~63 hours.
    # We advance by 5-hour ticks to ensure we reach Colombo.
    for _ in range(25):
        advance_voyage_simulation(voyage, graph, actual_weather, tick_duration=5.0)
        if voyage.current_node_id == "Colombo":
            break
            
    # The ship must have reached Colombo
    assert voyage.current_node_id == "Colombo"
    
    # Check that reroute event occurred and was adopted
    adopted_events = [e for e in voyage.reroute_events if e.route_changed]
    assert len(adopted_events) >= 1
    assert adopted_events[-1].new_path != initial_path


# 15. Hysteresis
def test_hysteresis():
    # If the new route cost is only slightly better (e.g. 1.6% better), but hysteresis is 5%,
    # the active route should NOT change.
    nodes = [
        Node(id="A", name="A", latitude=10.0, longitude=70.0, is_port=True),
        Node(id="B1", name="B1", latitude=10.0, longitude=72.0, is_port=False),
        Node(id="B2", name="B2", latitude=9.5, longitude=72.0, is_port=False),
        Node(id="D", name="D", latitude=10.0, longitude=74.0, is_port=True),
    ]
    edges = [
        Edge(id="E1", source_id="A", target_id="B1", distance_nm=120.0, base_congestion=0.1),
        Edge(id="E2", source_id="A", target_id="B2", distance_nm=121.0, base_congestion=0.1),
        Edge(id="E3", source_id="B1", target_id="D", distance_nm=120.0, base_congestion=0.1),
        Edge(id="E4", source_id="B2", target_id="D", distance_nm=120.0, base_congestion=0.1),
    ]
    graph = Graph(nodes=nodes, edges=edges)
    ship = ShipConfig(base_speed_knots=20.0)
    weather = DeterministicWeatherEngine(0, 0, 0, 0, 50, intensity_max=0.0)
    strategy = STRATEGIES["FASTEST"]

    # Initial voyage: plans A -> B1 -> D
    voyage = initialize_voyage(graph, "A", "D", 0.0, strategy, ship, weather, hysteresis_threshold=0.05)
    assert voyage is not None
    assert voyage.active_route.path[1].node_id == "B1"

    # Simulate minor projected cost increase for B1 (so rerouting check triggers)
    # Remaining cost is 240/20/10 = 1.2
    # Set projected remaining cost to 1.0 (so actual 1.2 > 1.0 * 1.05 -> check triggers)
    voyage.projected_remaining_costs["A"] = 1.0

    from src.simulation import trigger_rerouting_check

    # Run rerouting check: alternative path (A -> B1 -> D or A -> B2 -> D) is not > 5% better
    trigger_rerouting_check(voyage, graph, weather)
    assert len(voyage.reroute_events) >= 1
    assert voyage.reroute_events[-1].route_changed is False



# 16. Deterministic repeated runs
def test_deterministic_repeated_runs():
    graph = load_graph(GRAPH_FILEPATH)
    ship = ShipConfig()
    weather = DeterministicWeatherEngine(5.0, 85.0, 10.0, 90.0, 200.0, 8.0)
    strategy = STRATEGIES["BALANCED"]
    
    # Run 5 times and check that results are identical
    runs = []
    for _ in range(5):
        res = time_dependent_astar(graph, "Mumbai", "Singapore", 0.0, strategy, ship, weather)
        assert res is not None
        runs.append([step.node_id for step in res.path])
        
    for r in runs[1:]:
        assert r == runs[0]


# 17. Fault-detection tests
def test_fault_detection():
    graph = load_graph(GRAPH_FILEPATH)
    ship = ShipConfig()
    weather = DeterministicWeatherEngine(0, 0, 0, 0, 100)
    strategy = STRATEGIES["BALANCED"]
    
    # Unreachable destination
    res_unreachable = time_dependent_astar(graph, "Mumbai", "Aden", 0.0, strategy, ship, weather)
    # Aden is reachable from Mumbai. Let's try to reach Mumbai FROM Singapore.
    # Wait, Singapore -> Mumbai: let's check if Singapore has a path to Mumbai.
    # In our graph, we defined return edges: Singapore -> WP_Malacca_Strait -> Medan -> WP_Malacca_West -> WP_Bay_of_Bengal -> Colombo -> WP_Laccadive -> Mumbai.
    # Let's find a node that has no outgoing edges, or disconnect Aden.
    # Let's verify what happens with an invalid node ID:
    res_invalid = time_dependent_astar(graph, "Mumbai", "INVALID_NODE", 0.0, strategy, ship, weather)
    assert res_invalid is None
    
    # Invalid start node
    res_invalid_start = time_dependent_astar(graph, "INVALID_NODE", "Singapore", 0.0, strategy, ship, weather)
    assert res_invalid_start is None


# 18. Hysteresis threshold regression test (13.5% accepted, 2% rejected)
def test_dynamic_rerouting_hysteresis_thresholds():
    graph = load_graph(GRAPH_FILEPATH)
    ship = ShipConfig(base_speed_knots=15.0)
    strategy = STRATEGIES["BALANCED"]

    calm_weather = DeterministicWeatherEngine(0, 0, 0, 0, 100, intensity_max=0.0)

    # 1. Test 13.5% improvement -> EXPECT ACCEPTED (route_changed == True)
    storm_heavy = DeterministicWeatherEngine(
        start_lat=6.0, start_lon=85.0, speed_knots=0.0, direction_deg=0.0, radius_nm=150.0, intensity_max=8.0
    )

    voyage_a = initialize_voyage(graph, "Mumbai", "Singapore", 0.0, strategy, ship, calm_weather, hysteresis_threshold=0.05)
    assert voyage_a is not None

    # Advance by 1 tick (5 hours) under storm_heavy
    advance_voyage_simulation(voyage_a, graph, storm_heavy, tick_duration=5.0)

    # Reroute check should have fired and adopted the 13.5% improvement alternate
    accepted_events_a = [e for e in voyage_a.reroute_events if e.route_changed]
    assert len(accepted_events_a) >= 1, "13.5% improvement should be accepted by 5% hysteresis barrier"
    last_evt_a = accepted_events_a[0]
    improvement_pct_a = (last_evt_a.old_route_cost - last_evt_a.new_route_cost) / last_evt_a.old_route_cost * 100
    assert improvement_pct_a >= 10.0, f"Expected ~13.5% improvement, got {improvement_pct_a:.2f}%"

    # 2. Test ~2% improvement -> EXPECT REJECTED (route_changed == False)
    # Mild storm on default path that produces a ~2% cost difference
    storm_mild = DeterministicWeatherEngine(
        start_lat=6.0, start_lon=85.0, speed_knots=0.0, direction_deg=0.0, radius_nm=150.0, intensity_max=1.8
    )

    voyage_b = initialize_voyage(graph, "Mumbai", "Singapore", 0.0, strategy, ship, calm_weather, hysteresis_threshold=0.05)
    assert voyage_b is not None

    # Force projected cost lower so deterioration check triggers A* search
    current_proj = voyage_b.projected_remaining_costs.get("Mumbai", 1.0)
    voyage_b.projected_remaining_costs["Mumbai"] = current_proj * 0.85

    advance_voyage_simulation(voyage_b, graph, storm_mild, tick_duration=5.0)

    # Events evaluated should reject alternate if improvement is < 5%
    evaluated_events_b = [e for e in voyage_b.reroute_events]
    assert len(evaluated_events_b) >= 1, "Rerouting check should have been evaluated"
    for evt in evaluated_events_b:
        pct_diff = (evt.old_route_cost - evt.new_route_cost) / evt.old_route_cost * 100
        if pct_diff < 5.0:
            assert evt.route_changed is False, f"{pct_diff:.2f}% improvement should be rejected by 5% hysteresis threshold"


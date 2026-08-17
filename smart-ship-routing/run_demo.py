"""
run_demo.py — Smart Ship Routing Engine Demonstration

Scenario: Voyage from Mumbai to Singapore under BALANCED strategy.
Initial route is planned under calm weather forecast conditions.
The simulation advances in 5-minute ticks under continuous moving weather.
Mid-edge, weather deterioration on the upcoming active corridor is detected,
triggering time-dependent A* re-planning and 5% hysteresis acceptance.
"""
from src.models import load_graph, Graph
from src.weather import DeterministicWeatherEngine
from src.optimizer import STRATEGIES, ShipConfig
from src.router import RoutingResult
from src.simulation import initialize_voyage, advance_voyage_simulation

GRAPH_FILEPATH = "traffic.json"


def calculate_route_metrics(graph: Graph, route: RoutingResult) -> dict:
    total_dist = 0.0
    for i in range(len(route.path) - 1):
        s1 = route.path[i].node_id
        s2 = route.path[i + 1].node_id
        edge = next((e for e in graph.get_outgoing_edges(s1) if e.target_id == s2), None)
        if edge:
            total_dist += edge.distance_nm
    return {
        "distance_nm": total_dist,
        "eta_hours": route.total_time,
        "fuel_tons": route.total_fuel,
        "safety_penalty": route.total_safety,
        "congestion_cost": route.total_congestion,
    }


def main():
    graph = load_graph(GRAPH_FILEPATH)
    ship = ShipConfig(base_speed_knots=15.0)
    strategy = STRATEGIES["BALANCED"]

    # 1. Define Forecast Weather (Calm conditions at T=0)
    forecast_weather = DeterministicWeatherEngine(
        start_lat=0.0, start_lon=0.0, speed_knots=0.0, direction_deg=0.0, radius_nm=100.0, intensity_max=0.0
    )

    # 2. Define Actual Weather (Deterministic moving storm heading West in Bay of Bengal)
    actual_weather = DeterministicWeatherEngine(
        start_lat=6.0, start_lon=88.0, speed_knots=5.0, direction_deg=270.0, radius_nm=180.0, intensity_max=9.5
    )

    # 3. Initialize Voyage at T=0 under Calm Forecast
    voyage = initialize_voyage(
        graph, "Mumbai", "Singapore", 0.0, strategy, ship, forecast_weather, hysteresis_threshold=0.05
    )
    if not voyage:
        print("Failed to initialize voyage!")
        return

    init_route = voyage.active_route
    init_metrics = calculate_route_metrics(graph, init_route)
    init_path_str = " -> ".join([s.node_id for s in init_route.path])

    print("======================================================================")
    print("INITIAL ROUTE")
    print("======================================================================")
    print(f"Time: 0h")
    print(f"Strategy: {strategy.name}")
    print(f"Route: {init_path_str}")
    print(f"Distance: {init_metrics['distance_nm']:.1f} nm")
    print(f"ETA: {init_metrics['eta_hours']:.2f} hours ({init_metrics['eta_hours'] / 24.0:.2f} days)")
    print(f"Fuel: {init_metrics['fuel_tons']:.2f} tons")
    print(f"Safety: {init_metrics['safety_penalty']:.2f}")
    print(f"Congestion: {init_metrics['congestion_cost']:.2f}")
    print(f"Evaluated Cost: {init_route.total_cost:.4f}")

    print("\n======================================================================")
    print("SIMULATION")
    print("======================================================================")

    tick_duration_hours = 5.0 / 60.0  # 5-minute ticks
    max_ticks = 100
    reroute_accepted = False

    for tick in range(1, max_ticks + 1):
        num_events_before = len(voyage.reroute_events)

        # Advance simulation by 1 tick (5 minutes) under actual weather
        advance_voyage_simulation(voyage, graph, actual_weather, tick_duration=tick_duration_hours)

        t_hours = voyage.current_time
        t_mins = int(round(t_hours * 60))
        storm_intensity = actual_weather.get_conditions(voyage.current_lat, voyage.current_lon, t_hours)

        # Print tick telemetry
        print(f"T+{t_mins:02d} min ({t_hours:.2f}h) | Position: ({voyage.current_lat:.2f}°N, {voyage.current_lon:.2f}°E) | Segment: {voyage.current_node_id}->next ({voyage.segment_distance_traveled:.1f}nm) | Weather: {storm_intensity:.2f}")

        # Check if a rerouting event occurred during this tick
        if len(voyage.reroute_events) > num_events_before:
            last_event = voyage.reroute_events[-1]
            if last_event.route_changed:
                reroute_accepted = True
                pct_impr = (last_event.old_route_cost - last_event.new_route_cost) / last_event.old_route_cost * 100.0

                print("\n======================================================================")
                print("WEATHER DETERIORATION DETECTED")
                print("======================================================================")
                print(f"Time: T+{t_mins} min ({t_hours:.2f}h)")
                print(f"Position: ({last_event.lat:.4f}°N, {last_event.lon:.4f}°E) [MID-EDGE on segment {voyage.current_node_id}]")
                print(f"Safety/Cost Deterioration: projected {voyage.projected_remaining_costs.get(voyage.current_node_id, 0.0):.4f} -> actual remaining {last_event.old_route_cost:.4f}")
                print(f"Reason: Storm intensity on upcoming corridor crossed deterioration threshold")

                print("\nREROUTING")
                print(f"Old remaining cost: {last_event.old_route_cost:.4f}")
                print(f"New remaining cost: {last_event.new_route_cost:.4f}")
                print(f"Improvement: {pct_impr:.2f}% (Threshold: 5.0%)")
                print("\n✓ REROUTE ACCEPTED")

                print("\n======================================================================")
                print("NEW ROUTE")
                print("======================================================================")
                new_path_str = " -> ".join(last_event.new_path)
                new_metrics = calculate_route_metrics(graph, voyage.active_route)
                print(f"Route: {new_path_str}")
                print(f"New Total Cost: {voyage.active_route.total_cost:.4f}")
                print(f"Total Time: {new_metrics['eta_hours']:.2f} hours")
                print(f"Total Fuel: {new_metrics['fuel_tons']:.2f} tons")
                print(f"Total Safety Penalty: {new_metrics['safety_penalty']:.2f}")
                print(f"Total Congestion: {new_metrics['congestion_cost']:.2f}")
                break

    if not reroute_accepted:
        print("\nNo reroute was adopted during simulation.")


if __name__ == "__main__":
    main()

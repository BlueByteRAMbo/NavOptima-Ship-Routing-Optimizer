"""
router.py — Time-dependent A* search engine for vessel routing.
"""
import math
import heapq
from typing import List, Dict, Tuple, Optional, Any
from pydantic import BaseModel
from src.models import Graph, Node, Edge
from src.haversine import haversine_distance
from src.optimizer import (
    OptimizationStrategy,
    ShipConfig,
    calculate_weather_modifiers,
    calculate_edge_cost,
    N_TIME,
    N_FUEL,
    N_SAFETY,
    N_CONGESTION,
)
from src.weather import BaseWeatherProvider


class RouteStep(BaseModel):
    node_id: str
    edge_id: Optional[str] = None
    arrival_time: float
    accumulated_cost: float
    segment_cost: float = 0.0
    segment_time: float = 0.0
    segment_fuel: float = 0.0
    segment_safety: float = 0.0
    segment_congestion: float = 0.0


class RoutingResult(BaseModel):
    path: List[RouteStep]
    total_cost: float
    total_time: float
    total_fuel: float
    total_safety: float
    total_congestion: float
    strategy_name: str


def _sample_edge_weather(
    src_lat: float,
    src_lon: float,
    tgt_lat: float,
    tgt_lon: float,
    distance_nm: float,
    start_time: float,
    ship: ShipConfig,
    weather_provider: BaseWeatherProvider,
) -> Tuple[float, float]:
    """
    Two-pass midpoint weather sampling to compute edge weather intensity and travel time.
    """
    mid_lat = (src_lat + tgt_lat) / 2.0
    mid_lon = (src_lon + tgt_lon) / 2.0

    base_speed = ship.base_speed_knots if ship.base_speed_knots > 0 else 15.0
    est_travel_time = distance_nm / base_speed
    t_mid_pass1 = start_time + (est_travel_time / 2.0)

    intensity_pass1 = weather_provider.get_conditions(mid_lat, mid_lon, t_mid_pass1)
    speed_mod1, _, _ = calculate_weather_modifiers(intensity_pass1)
    eff_speed1 = base_speed * speed_mod1
    travel_time1 = distance_nm / eff_speed1 if eff_speed1 > 0 else 999999.0

    t_mid_pass2 = start_time + (travel_time1 / 2.0)
    intensity_pass2 = weather_provider.get_conditions(mid_lat, mid_lon, t_mid_pass2)

    intensity = max(intensity_pass1, intensity_pass2)
    speed_mod, _, _ = calculate_weather_modifiers(intensity)
    eff_speed = base_speed * speed_mod
    travel_time = distance_nm / eff_speed if eff_speed > 0 else 999999.0

    return intensity, travel_time


def calculate_heuristic(
    arg1: Any,
    arg2: Any,
    arg3: Any = None,
    arg4: Any = None,
    arg5: Any = None,
) -> float:
    """
    Admissible heuristic for time-dependent A*.
    Calculates lower bound on cost from current position to target node using Haversine distance.
    Supports signatures:
      - calculate_heuristic(start_node, target_node, strategy, ship)
      - calculate_heuristic(start_lat, start_lon, target_node, strategy, ship)
    """
    if isinstance(arg1, Node):
        lat, lon = arg1.latitude, arg1.longitude
        target_node = arg2
        strategy = arg3
        ship = arg4
    else:
        lat, lon = float(arg1), float(arg2)
        target_node = arg3
        strategy = arg4
        ship = arg5

    if target_node is None:
        return 0.0

    d_hav = haversine_distance(lat, lon, target_node.latitude, target_node.longitude)
    base_speed = ship.base_speed_knots if (ship and ship.base_speed_knots > 0) else 15.0
    base_fuel_rate = ship.base_fuel_rate if (ship and ship.base_fuel_rate > 0) else 1.0

    min_time = d_hav / base_speed
    min_fuel = base_fuel_rate * min_time

    w_time = strategy.w_time if strategy else 1.0
    w_fuel = strategy.w_fuel if strategy else 0.0

    h_cost = (w_time * (min_time / N_TIME)) + (w_fuel * (min_fuel / N_FUEL))
    return h_cost


def time_dependent_astar(
    graph: Graph,
    start_node_id: str,
    target_node_id: str,
    start_time: float,
    strategy: OptimizationStrategy,
    ship: ShipConfig,
    weather_provider: BaseWeatherProvider,
    start_lat: Optional[float] = None,
    start_lon: Optional[float] = None,
) -> Optional[RoutingResult]:
    """
    Time-dependent A* search algorithm for optimal maritime routing.
    """
    try:
        start_node = graph.get_node(start_node_id)
        target_node = graph.get_node(target_node_id)
    except KeyError:
        return None

    if start_node_id == target_node_id:
        init_step = RouteStep(
            node_id=start_node_id,
            arrival_time=start_time,
            accumulated_cost=0.0,
        )
        return RoutingResult(
            path=[init_step],
            total_cost=0.0,
            total_time=0.0,
            total_fuel=0.0,
            total_safety=0.0,
            total_congestion=0.0,
            strategy_name=strategy.name,
        )

    cur_lat = start_lat if start_lat is not None else start_node.latitude
    cur_lon = start_lon if start_lon is not None else start_node.longitude

    initial_h = calculate_heuristic(cur_lat, cur_lon, target_node, strategy, ship)
    initial_step = RouteStep(
        node_id=start_node_id,
        arrival_time=start_time,
        accumulated_cost=0.0,
    )

    # Priority queue item: (f_cost, counter, node_id, arrival_time, g_cost, fuel_sum, safety_sum, cong_sum, path_steps, cur_lat, cur_lon)
    counter = 0
    pq = [(initial_h, counter, start_node_id, start_time, 0.0, 0.0, 0.0, 0.0, [initial_step], cur_lat, cur_lon)]

    # Visited states: visited[node_id] = list of (g_cost, arrival_time)
    visited: Dict[str, List[Tuple[float, float]]] = {}

    while pq:
        f_cost, _, curr_id, curr_time, g_cost, fuel_sum, safety_sum, cong_sum, path_steps, c_lat, c_lon = heapq.heappop(pq)

        if curr_id == target_node_id:
            total_time = curr_time - start_time
            return RoutingResult(
                path=path_steps,
                total_cost=g_cost,
                total_time=total_time,
                total_fuel=fuel_sum,
                total_safety=safety_sum,
                total_congestion=cong_sum,
                strategy_name=strategy.name,
            )

        # Domination check
        dominated = False
        if curr_id in visited:
            for prev_g, prev_t in visited[curr_id]:
                if prev_g <= g_cost + 1e-9 and abs(prev_t - curr_time) < 1e-4:
                    dominated = True
                    break
        if dominated:
            continue

        if curr_id not in visited:
            visited[curr_id] = []
        visited[curr_id].append((g_cost, curr_time))

        # Explore outgoing edges
        for edge in graph.get_outgoing_edges(curr_id):
            nxt_id = edge.target_id

            # Avoid simple cycle in current path
            if any(step.node_id == nxt_id for step in path_steps):
                continue

            nxt_node = graph.get_node(nxt_id)
            intensity, seg_time = _sample_edge_weather(
                c_lat, c_lon, nxt_node.latitude, nxt_node.longitude,
                edge.distance_nm, curr_time, ship, weather_provider
            )

            seg_cost, seg_t, seg_fuel, seg_safety, seg_cong = calculate_edge_cost(
                edge.distance_nm, edge.base_congestion, intensity, ship, strategy
            )

            nxt_time = curr_time + seg_t
            nxt_g = g_cost + seg_cost
            nxt_fuel = fuel_sum + seg_fuel
            nxt_safety = safety_sum + seg_safety
            nxt_cong = cong_sum + seg_cong

            # Domination check before pushing
            if nxt_id in visited:
                skip_edge = False
                for prev_g, prev_t in visited[nxt_id]:
                    if prev_g <= nxt_g + 1e-9 and abs(prev_t - nxt_time) < 1e-4:
                        skip_edge = True
                        break
                if skip_edge:
                    continue

            h = calculate_heuristic(nxt_node.latitude, nxt_node.longitude, target_node, strategy, ship)
            nxt_f = nxt_g + h

            step = RouteStep(
                node_id=nxt_id,
                edge_id=edge.id,
                arrival_time=nxt_time,
                accumulated_cost=nxt_g,
                segment_cost=seg_cost,
                segment_time=seg_t,
                segment_fuel=seg_fuel,
                segment_safety=seg_safety,
                segment_congestion=seg_cong,
            )

            counter += 1
            heapq.heappush(pq, (
                nxt_f, counter, nxt_id, nxt_time, nxt_g, nxt_fuel, nxt_safety, nxt_cong,
                path_steps + [step], nxt_node.latitude, nxt_node.longitude
            ))

    return None


def time_dependent_astar_from_node(
    graph: Graph,
    start_node_id: str,
    target_node_id: str,
    start_time: float,
    strategy: OptimizationStrategy,
    ship: ShipConfig,
    weather_provider: BaseWeatherProvider,
) -> Optional[RoutingResult]:
    """
    Convenience wrapper for starting A* search directly from a node.
    """
    return time_dependent_astar(
        graph, start_node_id, target_node_id, start_time, strategy, ship, weather_provider
    )

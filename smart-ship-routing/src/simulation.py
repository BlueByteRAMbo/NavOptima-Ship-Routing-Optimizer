"""
simulation.py — Voyage state machine with dynamic mid-edge rerouting.

Fix 2: Rerouting uses the ship's ACTUAL physical position (current_lat, current_lon)
       as the A* start, not the last completed waypoint. When mid-edge, the already-
       travelled portion of the current edge is preserved; A* is called to plan from
       the next reachable waypoint onward.

Fix 7: Rerouting check runs on EVERY simulation tick (not only at waypoints).
       A* is only invoked if the cheap deterioration check crosses the threshold.
"""
from typing import List, Dict, Any, Optional, Tuple
import uuid
from pydantic import BaseModel, Field, ConfigDict
from src.models import Graph, Node, Edge
from src.weather import BaseWeatherProvider
from src.optimizer import (
    OptimizationStrategy,
    ShipConfig,
    calculate_weather_modifiers,
    calculate_edge_cost,
    N_TIME,
)
from src.router import (
    time_dependent_astar,
    time_dependent_astar_from_node,
    RoutingResult,
    RouteStep,
    _sample_edge_weather,
)


class RerouteEvent(BaseModel):
    time: float
    lat: float
    lon: float
    node_id: str               # last completed waypoint (or "MID_EDGE")
    old_route_cost: float
    new_route_cost: float
    route_changed: bool
    old_path: List[str]
    new_path: List[str]


class Voyage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_node_id: str
    target_node_id: str
    start_time: float
    current_time: float
    strategy: OptimizationStrategy
    ship: ShipConfig
    hysteresis_threshold: float = 0.05

    # ── Physical position ────────────────────────────────────────────────────
    current_node_id: str           # last waypoint reached (used for bookkeeping)
    current_lat: float
    current_lon: float
    current_segment_idx: int = 0   # index in active_route.path of the edge being traversed
    segment_distance_traveled: float = 0.0
    is_completed: bool = False

    # ── Route state ──────────────────────────────────────────────────────────
    active_route: RoutingResult
    # projected_remaining_costs[node_id] = cost from that node to target under
    # the weather forecast at the time the route was computed.
    projected_remaining_costs: Dict[str, float] = {}

    # ── Telemetry ────────────────────────────────────────────────────────────
    history: List[Dict[str, Any]] = []
    reroute_events: List[RerouteEvent] = []


# ─────────────────────────────────────────────────────────────────────────────
# Initialisation
# ─────────────────────────────────────────────────────────────────────────────

def initialize_voyage(
    graph: Graph,
    start_node_id: str,
    target_node_id: str,
    start_time: float,
    strategy: OptimizationStrategy,
    ship: ShipConfig,
    weather_provider: BaseWeatherProvider,
    hysteresis_threshold: float = 0.05,
) -> Optional[Voyage]:
    """Compute initial route and return an initialised Voyage."""
    initial_route = time_dependent_astar_from_node(
        graph, start_node_id, target_node_id, start_time, strategy, ship, weather_provider
    )
    if not initial_route:
        return None

    start_node = graph.get_node(start_node_id)
    projected = _build_projected_costs(initial_route)

    voyage = Voyage(
        start_node_id=start_node_id,
        target_node_id=target_node_id,
        start_time=start_time,
        current_time=start_time,
        strategy=strategy,
        ship=ship,
        hysteresis_threshold=hysteresis_threshold,
        current_node_id=start_node_id,
        current_lat=start_node.latitude,
        current_lon=start_node.longitude,
        active_route=initial_route,
        projected_remaining_costs=projected,
    )
    voyage.history.append(_make_history_entry(voyage, weather_provider))
    return voyage


def _build_projected_costs(route: RoutingResult) -> Dict[str, float]:
    """Return {node_id: remaining_cost_from_that_node} for every step in route."""
    total = route.total_cost
    accum = 0.0
    result: Dict[str, float] = {}
    for step in route.path:
        result[step.node_id] = total - accum
        accum += step.segment_cost
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Remaining-cost evaluator
# ─────────────────────────────────────────────────────────────────────────────

def _evaluate_remaining_cost(
    graph: Graph,
    route_path: List[RouteStep],
    start_segment_idx: int,
    segment_distance_already_traveled: float,
    current_lat: float,
    current_lon: float,
    current_time: float,
    ship: ShipConfig,
    strategy: OptimizationStrategy,
    weather_provider: BaseWeatherProvider,
) -> Tuple[float, float, float, float, float]:
    """
    Evaluate remaining route cost from the ship's current position.

    If mid-edge, only counts the REMAINING portion of the current segment
    plus all future segments.
    """
    total_cost = total_time = total_fuel = total_safety = total_cong = 0.0
    t = current_time

    for i in range(start_segment_idx, len(route_path) - 1):
        curr_step = route_path[i]
        next_step = route_path[i + 1]

        edge = next(
            (e for e in graph.get_outgoing_edges(curr_step.node_id)
             if e.target_id == next_step.node_id),
            None
        )
        if edge is None:
            raise ValueError(f"No edge {curr_step.node_id} -> {next_step.node_id}")

        # For the current segment: only remaining distance
        if i == start_segment_idx:
            remaining_dist = edge.distance_nm - segment_distance_already_traveled
            # proportion of the segment remaining
            frac = remaining_dist / edge.distance_nm if edge.distance_nm > 0 else 0.0
            effective_dist = remaining_dist
            effective_cong = edge.base_congestion * remaining_dist
        else:
            effective_dist = edge.distance_nm
            effective_cong = edge.base_congestion * edge.distance_nm
            frac = 1.0

        src_node = graph.get_node(curr_step.node_id)
        tgt_node = graph.get_node(next_step.node_id)
        intensity, _ = _sample_edge_weather(
            src_node.latitude, src_node.longitude,
            tgt_node.latitude, tgt_node.longitude,
            effective_dist, t, ship, weather_provider,
        )

        cost, travel_time, fuel, safety, cong = calculate_edge_cost(
            effective_dist, edge.base_congestion, intensity, ship, strategy
        )
        total_cost += cost
        total_time += travel_time
        total_fuel += fuel
        total_safety += safety
        total_cong += cong
        t += travel_time

    return total_cost, total_time, total_fuel, total_safety, total_cong


# ─────────────────────────────────────────────────────────────────────────────
# Fix 7 — Mid-tick rerouting check (called every tick, runs A* only if needed)
# ─────────────────────────────────────────────────────────────────────────────

def trigger_rerouting_check(
    voyage: Voyage,
    graph: Graph,
    weather_provider: BaseWeatherProvider,
) -> None:
    """
    Evaluate whether the remaining route has deteriorated enough to warrant re-planning.
    Fix 2: A* is called from physical position / next waypoint.
    Fix 7: Called on every simulation tick (mid-edge is fine).
    """
    curr_idx = voyage.current_segment_idx
    curr_t = voyage.current_time
    curr_lat = voyage.current_lat
    curr_lon = voyage.current_lon
    curr_node = voyage.current_node_id
    path = voyage.active_route.path

    if curr_idx >= len(path) - 1:
        return

    curr_step = path[curr_idx]
    next_step = path[curr_idx + 1]
    edge = next(
        (e for e in graph.get_outgoing_edges(curr_step.node_id)
         if e.target_id == next_step.node_id),
        None
    )

    # ── 1. Calculate ETA and segment cost to reach the next waypoint ─────────
    if voyage.segment_distance_traveled == 0.0:
        astar_start_id = curr_node
        eta_start = curr_t
        cost_to_next_wp = 0.0
        remaining_dist_on_edge = 0.0
        start_slice_idx = curr_idx + 1
    else:
        astar_start_id = next_step.node_id
        if edge is None:
            return
        remaining_dist_on_edge = edge.distance_nm - voyage.segment_distance_traveled
        storm_now = weather_provider.get_conditions(curr_lat, curr_lon, curr_t)
        speed_mod, _, _ = calculate_weather_modifiers(storm_now)
        eff_speed = voyage.ship.base_speed_knots * speed_mod
        time_to_next_wp = remaining_dist_on_edge / eff_speed if eff_speed > 0 else 0.0
        eta_start = curr_t + time_to_next_wp
        cost_to_next_wp, *_ = calculate_edge_cost(
            remaining_dist_on_edge, edge.base_congestion, storm_now, voyage.ship, voyage.strategy
        )
        start_slice_idx = curr_idx + 2

    # ── 2. Evaluate current remaining route cost under time-dependent model ──
    if voyage.segment_distance_traveled == 0.0:
        remaining_cost, *_ = _evaluate_remaining_cost(
            graph, path, curr_idx, 0.0,
            curr_lat, curr_lon, curr_t,
            voyage.ship, voyage.strategy, weather_provider
        )
    else:
        if curr_idx + 1 < len(path) - 1:
            next_node = graph.get_node(next_step.node_id)
            future_cost, *_ = _evaluate_remaining_cost(
                graph, path, curr_idx + 1, 0.0,
                next_node.latitude, next_node.longitude, eta_start,
                voyage.ship, voyage.strategy, weather_provider
            )
        else:
            future_cost = 0.0
        remaining_cost = cost_to_next_wp + future_cost

    # ── 3. Deterioration check against projected remaining cost ──────────────
    projected_from_node = voyage.projected_remaining_costs.get(curr_node, remaining_cost)
    frac_remaining = 1.0
    if edge and edge.distance_nm > 0:
        frac_remaining = max(0.0, (edge.distance_nm - voyage.segment_distance_traveled) / edge.distance_nm)
    proj_remaining = projected_from_node * frac_remaining

    if remaining_cost <= proj_remaining * (1.0 + voyage.hysteresis_threshold):
        return  # No significant deterioration — skip A*

    # ── 4. Run A* from next waypoint / current position at eta_start ─────────
    try:
        astar_start_node = graph.get_node(astar_start_id)
    except KeyError:
        return

    alternative = time_dependent_astar(
        graph,
        astar_start_id,
        voyage.target_node_id,
        eta_start,
        voyage.strategy,
        voyage.ship,
        weather_provider,
        start_lat=astar_start_node.latitude,
        start_lon=astar_start_node.longitude,
    )

    old_path = [s.node_id for s in path]

    if alternative is None:
        voyage.reroute_events.append(RerouteEvent(
            time=curr_t, lat=curr_lat, lon=curr_lon,
            node_id=curr_node,
            old_route_cost=remaining_cost, new_route_cost=remaining_cost,
            route_changed=False, old_path=old_path, new_path=old_path,
        ))
        return

    # ── 5. Total alternative remaining cost ──────────────────────────────────
    total_alt_cost = cost_to_next_wp + alternative.total_cost

    # ── 6. Hysteresis comparison ─────────────────────────────────────────────
    if total_alt_cost <= remaining_cost * (1.0 - voyage.hysteresis_threshold):
        completed_steps = list(path[:start_slice_idx])
        offset = completed_steps[-1].accumulated_cost if completed_steps else 0.0

        new_path_steps = list(completed_steps)
        for step in alternative.path[1:]:
            ns = step.model_copy()
            ns.accumulated_cost += offset
            new_path_steps.append(ns)

        new_route = RoutingResult(
            path=new_path_steps,
            total_cost=offset + alternative.total_cost,
            total_time=sum(s.segment_time for s in new_path_steps),
            total_fuel=sum(s.segment_fuel for s in new_path_steps),
            total_safety=sum(s.segment_safety for s in new_path_steps),
            total_congestion=sum(s.segment_congestion for s in new_path_steps),
            strategy_name=voyage.strategy.name,
        )

        new_path = [s.node_id for s in new_route.path]
        is_changed = (new_path != old_path)
        voyage.reroute_events.append(RerouteEvent(
            time=curr_t, lat=curr_lat, lon=curr_lon,
            node_id=curr_node,
            old_route_cost=remaining_cost,
            new_route_cost=total_alt_cost,
            route_changed=is_changed,
            old_path=old_path,
            new_path=new_path,
        ))
        voyage.active_route = new_route
        new_proj = _build_projected_costs(alternative)
        voyage.projected_remaining_costs.update(new_proj)
    else:
        voyage.reroute_events.append(RerouteEvent(
            time=curr_t, lat=curr_lat, lon=curr_lon,
            node_id=curr_node,
            old_route_cost=remaining_cost,
            new_route_cost=total_alt_cost,
            route_changed=False,
            old_path=old_path,
            new_path=old_path,
        ))



# ─────────────────────────────────────────────────────────────────────────────
# Main simulation tick
# ─────────────────────────────────────────────────────────────────────────────

def advance_voyage_simulation(
    voyage: Voyage,
    graph: Graph,
    weather_provider: BaseWeatherProvider,
    tick_duration: float = 1.0,
) -> None:
    """
    Advance simulation clock by tick_duration hours.

    Fix 7: rerouting check runs every tick (mid-edge is fine).
    Fix 2: position is tracked continuously; rerouting uses actual lat/lon.
    """
    if voyage.is_completed:
        return

    # ── Fix 7: check for rerouting at the START of every tick ────────────────
    if not voyage.is_completed:
        trigger_rerouting_check(voyage, graph, weather_provider)

    time_remaining = tick_duration

    while time_remaining > 0.0 and not voyage.is_completed:
        path = voyage.active_route.path

        if voyage.current_segment_idx >= len(path) - 1:
            voyage.is_completed = True
            break

        source_step = path[voyage.current_segment_idx]
        next_step   = path[voyage.current_segment_idx + 1]
        source_node = graph.get_node(source_step.node_id)
        target_node = graph.get_node(next_step.node_id)

        edge = next(
            (e for e in graph.get_outgoing_edges(source_node.id)
             if e.target_id == target_node.id),
            None
        )
        if edge is None:
            raise ValueError(f"Invalid edge in route: {source_node.id} -> {target_node.id}")

        edge_distance = edge.distance_nm

        # Query weather at current position
        storm_intensity = weather_provider.get_conditions(
            voyage.current_lat, voyage.current_lon, voyage.current_time
        )
        speed_mod, _, _ = calculate_weather_modifiers(storm_intensity)
        effective_speed = voyage.ship.base_speed_knots * speed_mod

        distance_ticked = effective_speed * time_remaining
        segment_remaining = edge_distance - voyage.segment_distance_traveled

        if distance_ticked < segment_remaining:
            # Mid-edge: update position and clock
            voyage.segment_distance_traveled += distance_ticked
            voyage.current_time += time_remaining
            time_remaining = 0.0

            fraction = voyage.segment_distance_traveled / edge_distance
            voyage.current_lat = source_node.latitude + fraction * (target_node.latitude - source_node.latitude)
            voyage.current_lon = source_node.longitude + fraction * (target_node.longitude - source_node.longitude)

        else:
            # Ship reaches next waypoint
            time_to_reach = segment_remaining / effective_speed
            voyage.current_time += time_to_reach
            time_remaining -= time_to_reach

            voyage.current_node_id = target_node.id
            voyage.current_lat = target_node.latitude
            voyage.current_lon = target_node.longitude
            voyage.segment_distance_traveled = 0.0
            voyage.current_segment_idx += 1

            voyage.history.append({
                "time": voyage.current_time,
                "lat": voyage.current_lat,
                "lon": voyage.current_lon,
                "current_node_id": voyage.current_node_id,
                "speed_knots": effective_speed,
                "storm_intensity": storm_intensity,
                "active_route_nodes": [s.node_id for s in voyage.active_route.path],
            })

            if voyage.current_segment_idx >= len(path) - 1:
                voyage.is_completed = True
                break

            # Rerouting check at waypoint arrival
            trigger_rerouting_check(voyage, graph, weather_provider)

    # Log end-of-tick position (if not already logged this tick)
    if not voyage.is_completed:
        last_t = voyage.history[-1]["time"] if voyage.history else None
        if last_t != voyage.current_time:
            voyage.history.append(_make_history_entry(voyage, weather_provider))


def _make_history_entry(voyage: Voyage, weather_provider: BaseWeatherProvider) -> Dict[str, Any]:
    storm = weather_provider.get_conditions(voyage.current_lat, voyage.current_lon, voyage.current_time)
    speed_mod, _, _ = calculate_weather_modifiers(storm)
    return {
        "time": voyage.current_time,
        "lat": voyage.current_lat,
        "lon": voyage.current_lon,
        "current_node_id": voyage.current_node_id,
        "speed_knots": voyage.ship.base_speed_knots * speed_mod,
        "storm_intensity": storm,
        "active_route_nodes": [s.node_id for s in voyage.active_route.path],
    }

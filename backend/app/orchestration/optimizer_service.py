"""
Optimizer Orchestration Service
================================
Adapter layer integrating smart-ship-routing's frozen time-dependent A* engine
with the FastAPI backend and frontend API contract.
"""

import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Ensure smart-ship-routing is importable without modifying its internal structure
ROUTING_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "smart-ship-routing")
)
if ROUTING_ROOT not in sys.path:
    sys.path.insert(0, ROUTING_ROOT)

from src.models import Graph, Node, load_graph
from src.optimizer import (
    STRATEGIES,
    OptimizationStrategy,
    ShipConfig,
)
from src.router import RoutingResult, time_dependent_astar
from src.simulation import Voyage, initialize_voyage, advance_voyage_simulation, _build_projected_costs
from src.weather import BaseWeatherProvider, DeterministicWeatherEngine
from src.haversine import haversine_distance

from backend.app.models.port import Port
from backend.app.models.route import (
    RouteRequest,
    RouteResponse,
    SimulationEvent,
    SimulationResponse,
    VoyageCreateRequest,
    VoyageStateResponse,
    TickRequest,
    TickResponse,
)
from backend.app.models.ship import DEFAULT_SHIPS, ShipProfile
from backend.app.services.copernicus_provider import CopernicusWeatherProvider
from backend.app.services.data_loader import get_ports_raw

# Path to the frozen traffic graph
GRAPH_FILEPATH = os.path.join(ROUTING_ROOT, "traffic.json")

# In-memory graph and voyage storage
_graph_instance: Optional[Graph] = None
_voyages_db: Dict[str, Voyage] = {}
_voyage_providers_db: Dict[str, BaseWeatherProvider] = {}
_voyage_request_db: Dict[str, VoyageCreateRequest] = {}


def get_routing_graph() -> Graph:
    """Loads and caches the frozen navigation graph."""
    global _graph_instance
    if _graph_instance is None:
        if not os.path.exists(GRAPH_FILEPATH):
            raise FileNotFoundError(f"Routing graph not found at {GRAPH_FILEPATH}")
        _graph_instance = load_graph(GRAPH_FILEPATH)
    return _graph_instance


# ----------------------------------------------------------------------
# Canonical Port ID <-> Graph Node ID Mapping & Resolution
# ----------------------------------------------------------------------

CANONICAL_TO_GRAPH: Dict[str, str] = {
    "mumbai": "Mumbai",
    "colombo": "Colombo",
    "singapore": "Singapore",
    "kochi": "Kochi",
    "yangon": "Yangon",
    "chennai": "Chennai",
    "visakhapatnam": "Visakhapatnam",
    "aden": "Aden",
    "male": "Male",
    "medan": "Medan",
    "mundra": "Mundra",
    "chattogram": "Chattogram",
    "jebel_ali": "Jebel_Ali",
    "salalah": "Salalah",
    "mombasa": "Mombasa",
    "dar_es_salaam": "Dar_Es_Salaam",
    "port_louis": "Port_Louis",
    "durban": "Durban",
    "port_klang": "Port_Klang",
    "karachi": "Karachi",
}


def normalize_port_identifier(raw_identifier: str) -> str:
    """Normalizes user input string to canonical port ID or graph node ID."""
    cleaned = raw_identifier.strip().lower()
    if "," in cleaned:
        cleaned = cleaned.split(",")[0].strip()
    if cleaned.startswith("port of "):
        cleaned = cleaned.replace("port of ", "").strip()
    if cleaned.startswith("port "):
        cleaned = cleaned.replace("port ", "").strip()
    if "/" in cleaned:
        cleaned = cleaned.split("/")[0].strip()
    return cleaned.replace(" ", "_").replace("-", "_")


def resolve_port_location(identifier: str) -> Tuple[Optional[str], Optional[float], Optional[float], str]:
    """Resolves an input identifier to (graph_node_id, latitude, longitude, display_name)."""
    norm = normalize_port_identifier(identifier)
    graph = get_routing_graph()

    # 1. Direct mapping to graph
    if norm in CANONICAL_TO_GRAPH:
        node_id = CANONICAL_TO_GRAPH[norm]
        try:
            node = graph.get_node(node_id)
            return node.id, node.latitude, node.longitude, node.name
        except KeyError:
            pass

    # 2. Check direct graph node names (case-insensitive)
    for node in graph.nodes:
        if node.id.lower() == norm or node.name.lower() == norm or node.id.lower() == identifier.lower():
            return node.id, node.latitude, node.longitude, node.name

    # 3. Check canonical ports.json
    raw_ports = get_ports_raw()
    for p in raw_ports:
        p_id = str(p.get("id", "")).lower()
        p_name = str(p.get("name", "")).lower()
        if p_id == norm or p_name == norm or norm in p_name:
            return None, float(p.get("lat", 0.0)), float(p.get("lon", 0.0)), p.get("name", identifier)

    return None, None, None, identifier


# ----------------------------------------------------------------------
# Optimization Strategy & Ship Configuration
# ----------------------------------------------------------------------

def resolve_strategy(optimization_mode: str) -> OptimizationStrategy:
    """Translates frontend optimization modes to frozen engine OptimizationStrategy."""
    mode = optimization_mode.strip().upper()
    if mode in STRATEGIES:
        return STRATEGIES[mode]
    if mode == "FASTEST":
        return STRATEGIES["FASTEST"]
    if mode == "SAFEST":
        return STRATEGIES["SAFEST"]
    if mode in ("LEAST_CONGESTED", "FUEL_EFFICIENT"):
        return STRATEGIES["LEAST_CONGESTED"]
    return STRATEGIES["BALANCED"]


def resolve_ship_config(ship_type: str) -> ShipConfig:
    """Translates ship selection into routing engine ShipConfig."""
    ship_key = ship_type.strip().lower()
    profile = DEFAULT_SHIPS.get(ship_key, DEFAULT_SHIPS["container"])
    return ShipConfig(
        base_speed_knots=profile.speed_knots,
        base_fuel_rate=profile.fuel_rate_mt_per_hour,
    )


def resolve_weather_provider(data_mode: str, storm: Optional[Dict[str, Any]] = None) -> BaseWeatherProvider:
    """Instantiates appropriate WeatherProvider based on data_mode."""
    mode = (data_mode or "HYBRID").strip().upper()
    
    overlay_storm = None
    if storm:
        overlay_storm = DeterministicWeatherEngine(
            start_lat=float(storm.get("start_lat", 6.0)),
            start_lon=float(storm.get("start_lon", 85.0)),
            speed_knots=float(storm.get("speed_knots", 8.0)),
            direction_deg=float(storm.get("direction_deg", 90.0)),
            radius_nm=float(storm.get("radius_nm", 150.0)),
            intensity_max=float(storm.get("intensity_max", 8.0)),
        )

    if mode in ("HYBRID", "COPERNICUS", "LIVE", "CACHED"):
        return CopernicusWeatherProvider(overlay_storm=overlay_storm)
    
    if overlay_storm:
        return overlay_storm
    
    # Calm mock provider for baseline mock calculations
    return DeterministicWeatherEngine(
        start_lat=0.0,
        start_lon=0.0,
        speed_knots=0.0,
        direction_deg=0.0,
        radius_nm=10.0,
        intensity_max=0.0,
    )


# ----------------------------------------------------------------------
# Core Route Optimization
# ----------------------------------------------------------------------

def calculate_optimal_route(request: RouteRequest) -> RouteResponse:
    """
    Computes optimal route using smart-ship-routing's frozen time-dependent A* engine.
    """
    graph = get_routing_graph()
    origin_raw = request.get_origin() or "mumbai"
    dest_raw = request.get_destination() or "colombo"
    opt_mode = request.get_optimization()
    ship_type = request.get_ship()
    data_mode = (request.data_mode or "HYBRID").upper()

    orig_node_id, orig_lat, orig_lon, orig_name = resolve_port_location(origin_raw)
    dest_node_id, dest_lat, dest_lon, dest_name = resolve_port_location(dest_raw)

    strategy = resolve_strategy(opt_mode)
    ship = resolve_ship_config(ship_type)
    weather_provider = resolve_weather_provider(data_mode)

    # Validate graph support for ports
    if not orig_node_id or not dest_node_id or orig_node_id == dest_node_id:
        unsupported = []
        if not orig_node_id:
            unsupported.append(orig_name or origin_raw)
        if not dest_node_id:
            unsupported.append(dest_name or dest_raw)
        
        reason = f"Routing graph vertex unavailable for port(s): {', '.join(unsupported)}. Route calculation disabled."
        return RouteResponse(
            coordinates=[],
            distance_km=0.0,
            eta_hours=0.0,
            fuel_mt=0.0,
            safety_score=0.0,
            reason=reason,
            strategy=strategy.name,
            data_mode=data_mode,
            data_status="UNAVAILABLE",
            routing_supported=False,
            path_nodes=[],
        )

    routing_result = time_dependent_astar(
        graph=graph,
        start_node_id=orig_node_id,
        target_node_id=dest_node_id,
        start_time=0.0,
        strategy=strategy,
        ship=ship,
        weather_provider=weather_provider,
    )

    if not routing_result or not routing_result.path:
        return RouteResponse(
            coordinates=[],
            distance_km=0.0,
            eta_hours=0.0,
            fuel_mt=0.0,
            safety_score=0.0,
            reason=f"No navigable path found between {orig_name} and {dest_name} under {strategy.name} strategy.",
            strategy=strategy.name,
            data_mode=data_mode,
            data_status="UNAVAILABLE",
            routing_supported=False,
            path_nodes=[],
        )

    coordinates: List[List[float]] = []
    total_dist_nm = 0.0

    for i, step in enumerate(routing_result.path):
        node = graph.get_node(step.node_id)
        coordinates.append([node.latitude, node.longitude])
        if i < len(routing_result.path) - 1:
            nxt = routing_result.path[i + 1].node_id
            edge = next((e for e in graph.get_outgoing_edges(step.node_id) if e.target_id == nxt), None)
            if edge:
                total_dist_nm += edge.distance_nm

    dist_km = round(total_dist_nm * 1.852, 1)
    eta_h = round(routing_result.total_time, 1)
    fuel_mt = round(routing_result.total_fuel, 1)
    safety_score = max(0.0, min(100.0, round(100.0 - routing_result.total_safety * 4.0, 1)))
    congestion_score = round(routing_result.total_congestion, 2)

    path_names = [graph.get_node(s.node_id).name for s in routing_result.path]
    path_nodes = [s.node_id for s in routing_result.path]
    
    reason = (
        f"{strategy.name} optimized A* route via {' -> '.join(path_names)}. "
        f"Computed over {data_mode} environmental data."
    )

    from backend.app.services.security import assess_route_security
    sec_eval = assess_route_security(coordinates)
    if sec_eval.get("advisories"):
        reason += f" Security Note: {'; '.join(sec_eval['advisories'])}"

    return RouteResponse(
        coordinates=coordinates,
        distance_km=dist_km,
        eta_hours=eta_h,
        fuel_mt=fuel_mt,
        safety_score=safety_score,
        congestion_score=congestion_score,
        total_cost=round(routing_result.total_cost, 4),
        reason=reason,
        strategy=strategy.name,
        data_mode=data_mode,
        data_status="CACHED" if data_mode in ("HYBRID", "COPERNICUS") else "MOCK",
        routing_supported=True,
        path_nodes=path_nodes,
        security_advisories=sec_eval.get("advisories", []),
        max_security_risk=sec_eval.get("max_risk_level", 0.0),
        intersected_security_zones=sec_eval.get("intersected_zones", []),
    )


# ----------------------------------------------------------------------
# Stateful Voyage Lifecycle Management
# ----------------------------------------------------------------------

def _build_route_response_from_routing_result(
    routing_result: RoutingResult,
    graph: Graph,
    strategy_name: str,
    data_mode: str,
) -> RouteResponse:
    coordinates = []
    total_dist_nm = 0.0
    for i, step in enumerate(routing_result.path):
        node = graph.get_node(step.node_id)
        coordinates.append([node.latitude, node.longitude])
        if i < len(routing_result.path) - 1:
            nxt = routing_result.path[i + 1].node_id
            edge = next((e for e in graph.get_outgoing_edges(step.node_id) if e.target_id == nxt), None)
            if edge:
                total_dist_nm += edge.distance_nm

    dist_km = round(total_dist_nm * 1.852, 1)
    eta_h = round(routing_result.total_time, 1)
    fuel_mt = round(routing_result.total_fuel, 1)
    safety_score = max(0.0, min(100.0, round(100.0 - routing_result.total_safety * 4.0, 1)))

    path_nodes = [s.node_id for s in routing_result.path]
    path_names = [graph.get_node(s.node_id).name for s in routing_result.path]

    from backend.app.services.security import assess_route_security
    sec_eval = assess_route_security(coordinates)

    return RouteResponse(
        coordinates=coordinates,
        distance_km=dist_km,
        eta_hours=eta_h,
        fuel_mt=fuel_mt,
        safety_score=safety_score,
        congestion_score=round(routing_result.total_congestion, 2),
        total_cost=round(routing_result.total_cost, 4),
        reason=f"Active voyage route via {' -> '.join(path_names)}",
        strategy=strategy_name,
        data_mode=data_mode,
        data_status="CACHED" if data_mode in ("HYBRID", "COPERNICUS") else "MOCK",
        routing_supported=True,
        path_nodes=path_nodes,
        security_advisories=sec_eval.get("advisories", []),
        max_security_risk=sec_eval.get("max_risk_level", 0.0),
        intersected_security_zones=sec_eval.get("intersected_zones", []),
    )


def create_voyage(req: VoyageCreateRequest) -> VoyageStateResponse:
    """Initializes a stateful voyage using the frozen simulation core."""
    graph = get_routing_graph()
    orig_node_id, _, _, orig_name = resolve_port_location(req.origin)
    dest_node_id, _, _, dest_name = resolve_port_location(req.destination)

    if not orig_node_id or not dest_node_id:
        raise ValueError(f"Port(s) '{req.origin}' or '{req.destination}' not supported in navigation graph.")

    strategy = resolve_strategy(req.optimization)
    ship = resolve_ship_config(req.ship)
    data_mode = (req.data_mode or "HYBRID").upper()
    weather_provider = resolve_weather_provider(data_mode, storm=req.storm)

    voyage = initialize_voyage(
        graph=graph,
        start_node_id=orig_node_id,
        target_node_id=dest_node_id,
        start_time=0.0,
        strategy=strategy,
        ship=ship,
        weather_provider=weather_provider,
        hysteresis_threshold=req.hysteresis_threshold or 0.05,
    )

    if not voyage:
        raise ValueError(f"Could not initialize voyage route between {orig_name} and {dest_name}.")

    _voyages_db[voyage.id] = voyage
    _voyage_providers_db[voyage.id] = weather_provider
    _voyage_request_db[voyage.id] = req

    active_route_res = _build_route_response_from_routing_result(
        voyage.active_route, graph, strategy.name, data_mode
    )

    return VoyageStateResponse(
        voyage_id=voyage.id,
        origin=orig_node_id,
        destination=dest_node_id,
        ship=req.ship,
        strategy=strategy.name,
        data_mode=data_mode,
        current_time=voyage.current_time,
        current_lat=voyage.current_lat,
        current_lon=voyage.current_lon,
        current_node_id=voyage.current_node_id,
        is_completed=voyage.is_completed,
        active_route=active_route_res,
        history=voyage.history,
        reroute_events=[e.model_dump() for e in voyage.reroute_events],
    )


def get_voyage(voyage_id: str) -> VoyageStateResponse:
    """Returns current state of active voyage."""
    if voyage_id not in _voyages_db:
        raise KeyError(f"Voyage '{voyage_id}' not found.")

    voyage = _voyages_db[voyage_id]
    graph = get_routing_graph()
    req = _voyage_request_db.get(voyage_id, VoyageCreateRequest(origin=voyage.start_node_id, destination=voyage.target_node_id))
    data_mode = req.data_mode.upper()

    active_route_res = _build_route_response_from_routing_result(
        voyage.active_route, graph, voyage.strategy.name, data_mode
    )

    return VoyageStateResponse(
        voyage_id=voyage.id,
        origin=voyage.start_node_id,
        destination=voyage.target_node_id,
        ship=req.ship,
        strategy=voyage.strategy.name,
        data_mode=data_mode,
        current_time=voyage.current_time,
        current_lat=voyage.current_lat,
        current_lon=voyage.current_lon,
        current_node_id=voyage.current_node_id,
        is_completed=voyage.is_completed,
        active_route=active_route_res,
        history=voyage.history,
        reroute_events=[e.model_dump() for e in voyage.reroute_events],
    )


def tick_voyage(voyage_id: str, tick_duration: float = 1.0) -> TickResponse:
    """Advances voyage simulation clock and evaluates hysteresis-based rerouting."""
    if voyage_id not in _voyages_db:
        raise KeyError(f"Voyage '{voyage_id}' not found.")

    voyage = _voyages_db[voyage_id]
    weather_provider = _voyage_providers_db[voyage_id]
    graph = get_routing_graph()
    req = _voyage_request_db.get(voyage_id, VoyageCreateRequest(origin=voyage.start_node_id, destination=voyage.target_node_id))
    data_mode = req.data_mode.upper()

    reroutes_before = len(voyage.reroute_events)
    advance_voyage_simulation(voyage, graph, weather_provider, tick_duration)

    rerouted_in_tick = False
    new_cost = None
    last_event_dict = None

    if len(voyage.reroute_events) > reroutes_before:
        last_event = voyage.reroute_events[-1]
        rerouted_in_tick = last_event.route_changed
        last_event_dict = last_event.model_dump()
        if rerouted_in_tick:
            new_cost = voyage.active_route.total_cost

    active_route_res = _build_route_response_from_routing_result(
        voyage.active_route, graph, voyage.strategy.name, data_mode
    )

    return TickResponse(
        voyage_id=voyage.id,
        current_time=voyage.current_time,
        current_node_id=voyage.current_node_id,
        current_lat=voyage.current_lat,
        current_lon=voyage.current_lon,
        is_completed=voyage.is_completed,
        active_route_nodes=[step.node_id for step in voyage.active_route.path],
        active_route=active_route_res,
        rerouted_in_tick=rerouted_in_tick,
        new_route_cost=new_cost,
        reroute_event=last_event_dict,
    )


# ----------------------------------------------------------------------
# Dynamic Simulation Event Recalculation (voyage-aware disruption)
# ----------------------------------------------------------------------


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Helper to compute Haversine distance in kilometers."""
    return haversine_distance(lat1, lon1, lat2, lon2) * 1.852


def _min_dist_to_segment_km(p_lat: float, p_lon: float, a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    """Computes minimum distance in km from point P to line segment AB by sampling points along the segment."""
    d_total = _haversine_km(a_lat, a_lon, b_lat, b_lon)
    if d_total < 1.0:
        return _haversine_km(p_lat, p_lon, a_lat, a_lon)
    num_samples = max(5, min(50, int(d_total / 25.0)))
    min_d = min(_haversine_km(p_lat, p_lon, a_lat, a_lon), _haversine_km(p_lat, p_lon, b_lat, b_lon))
    for i in range(1, num_samples):
        frac = i / num_samples
        s_lat = a_lat + frac * (b_lat - a_lat)
        s_lon = a_lon + frac * (b_lon - a_lon)
        d = _haversine_km(p_lat, p_lon, s_lat, s_lon)
        if d < min_d:
            min_d = d
    return min_d


def handle_simulation_event(event: SimulationEvent) -> SimulationResponse:
    """
    Evaluates dynamic disruption events strictly bound to the user's active voyage.
    
    Causal Chain & Decision Architecture:
    1. Resolves active voyage context (origin, destination, ship, strategy, data_mode, current position, current_time).
    2. Filters active route nodes to remaining nodes from current_segment_idx onward.
    3. Checks spatial relevance against remaining route segments and current ship position.
       If event is near already-traversed nodes (behind vessel), flags spatially_relevant=False
       with explicit reason: "Disruption affects route segment already traversed at t=X.Xh."
    4. Evaluates baseline remaining route cost under weather provider vs disrupted weather provider.
    5. Computes authoritative ETA, fuel, safety, and congestion deltas.
    6. Persists updated active_route and weather provider to backend voyage state.
    7. Formats structured, human-readable reason explaining WHY rerouting occurred or was rejected by hysteresis.
    """
    graph = get_routing_graph()

    # 1. Resolve Active Voyage Context
    voyage_id = event.voyage_id
    voyage: Optional[Voyage] = None
    req: Optional[VoyageCreateRequest] = None

    if voyage_id:
        if voyage_id in _voyages_db:
            voyage = _voyages_db[voyage_id]
            req = _voyage_request_db.get(voyage_id)
        else:
            raise KeyError(f"Voyage '{voyage_id}' not found. Please create a voyage session first.")
    elif len(_voyages_db) > 0:
        voyage_id = list(_voyages_db.keys())[-1]
        voyage = _voyages_db[voyage_id]
        req = _voyage_request_db.get(voyage_id)
    else:
        # Automatically initialize default voyage session for standalone simulation testing
        default_req = VoyageCreateRequest(
            origin="mumbai",
            destination="colombo",
            ship="container",
            optimization="balanced",
        )
        create_voyage(default_req)
        voyage_id = list(_voyages_db.keys())[-1]
        voyage = _voyages_db[voyage_id]
        req = _voyage_request_db.get(voyage_id)

    if not voyage or not req:
        raise KeyError("No active voyage session found. Please create a voyage session first.")

    orig_id         = voyage.start_node_id
    dest_id         = voyage.target_node_id
    strategy        = voyage.strategy
    ship            = voyage.ship
    data_mode       = req.data_mode.upper()
    current_node_id = voyage.current_node_id
    start_time      = voyage.current_time
    curr_lat        = voyage.current_lat
    curr_lon        = voyage.current_lon
    curr_seg_idx    = voyage.current_segment_idx
    hysteresis      = voyage.hysteresis_threshold

    orig_node = graph.get_node(orig_id)
    dest_node = graph.get_node(dest_id)
    orig_name = orig_node.name if orig_node else orig_id
    dest_name = dest_node.name if dest_node else dest_id

    # Active path steps & coordinates
    all_path_steps = voyage.active_route.path
    all_path_nodes = [step.node_id for step in all_path_steps]
    old_coords     = [[graph.get_node(nid).latitude, graph.get_node(nid).longitude]
                      for nid in all_path_nodes if graph.get_node(nid)]

    # 2. Extract REMAINING route nodes (if departed current waypoint, start from next waypoint)
    if voyage and voyage.segment_distance_traveled > 20.0 and (curr_seg_idx + 1) < len(all_path_nodes):
        remaining_node_ids = all_path_nodes[curr_seg_idx + 1:]
    else:
        remaining_node_ids = all_path_nodes[curr_seg_idx:] if curr_seg_idx < len(all_path_nodes) else all_path_nodes
    remaining_nodes    = [graph.get_node(nid) for nid in remaining_node_ids if graph.get_node(nid)]
    
    # Measure min distance from event center to ship's current position and remaining route segments
    min_dist_to_ship_km = _haversine_km(event.lat, event.lon, curr_lat, curr_lon)
    remaining_coords = [[curr_lat, curr_lon]] + [[n.latitude, n.longitude] for n in remaining_nodes]
    min_dist_to_remaining_km = min_dist_to_ship_km
    for i in range(len(remaining_coords) - 1):
        d_seg = _min_dist_to_segment_km(
            event.lat, event.lon,
            remaining_coords[i][0], remaining_coords[i][1],
            remaining_coords[i+1][0], remaining_coords[i+1][1],
        )
        if d_seg < min_dist_to_remaining_km:
            min_dist_to_remaining_km = d_seg

    # Measure min distance to ALL route segments (to detect if event is behind ship)
    all_coords = [[graph.get_node(nid).latitude, graph.get_node(nid).longitude] for nid in all_path_nodes if graph.get_node(nid)]
    min_dist_to_all_km = min_dist_to_remaining_km
    for i in range(len(all_coords) - 1):
        d_seg = _min_dist_to_segment_km(
            event.lat, event.lon,
            all_coords[i][0], all_coords[i][1],
            all_coords[i+1][0], all_coords[i+1][1],
        )
        if d_seg < min_dist_to_all_km:
            min_dist_to_all_km = d_seg

    label = event.label or f"{event.type.replace('_', ' ').capitalize()} Disruption"

    # Baseline weather & route evaluation
    baseline_weather = _voyage_providers_db.get(voyage_id, resolve_weather_provider(data_mode))
    baseline_route   = time_dependent_astar(
        graph=graph, start_node_id=current_node_id, target_node_id=dest_id,
        start_time=start_time, strategy=strategy, ship=ship,
        weather_provider=baseline_weather,
        start_lat=curr_lat, start_lon=curr_lon,
    ) or voyage.active_route

    def _base_resp():
        return _build_route_response_from_routing_result(baseline_route, graph, strategy.name, data_mode)

    # Check if event is BEHIND vessel (close to past nodes but far from remaining nodes)
    threshold_dist = event.radius_km + 300.0
    if min_dist_to_all_km <= threshold_dist and min_dist_to_remaining_km > threshold_dist:
        reason = (
            f"{label} at ({event.lat:.2f}°N, {event.lon:.2f}°E) affects route segment already traversed at t={start_time:.1f}h. "
            f"No impact on remaining voyage to {dest_name}."
        )
        base_r = _base_resp()
        return SimulationResponse(
            voyage_id=voyage_id, origin=orig_id, destination=dest_id,
            spatially_relevant=False, old_route=old_coords, new_route=old_coords,
            reason=reason, eta_change_hours=0.0, fuel_change_mt=0.0,
            safety_change=0.0, congestion_change=0.0, rerouted=False,
            active_route=base_r,
            event_type=event.type, timestamp=start_time, severity=event.severity,
            eta_before=base_r.eta_hours if base_r else 0.0,
            eta_after=base_r.eta_hours if base_r else 0.0,
            fuel_before=base_r.fuel_mt if base_r else 0.0,
            fuel_after=base_r.fuel_mt if base_r else 0.0,
            safety_before=base_r.safety_score if base_r else 0.0,
            safety_after=base_r.safety_score if base_r else 0.0,
            cost_improvement_percent=0.0,
            hysteresis_threshold_percent=round(hysteresis * 100.0, 1),
            decision="EVENT_BEHIND_VESSEL",
            security_advisories=base_r.security_advisories if base_r else [],
            max_security_risk=base_r.max_security_risk if base_r else 0.0,
            intersected_security_zones=base_r.intersected_security_zones if base_r else [],
        )

    # Check if event is spatially irrelevant to the entire route
    if min_dist_to_remaining_km > threshold_dist:
        reason = (
            f"{label} at ({event.lat:.2f}°N, {event.lon:.2f}°E) is {min_dist_to_remaining_km:.0f} km "
            f"from remaining route (threshold {threshold_dist:.0f} km). Spatially irrelevant to {orig_name} → {dest_name}."
        )
        base_r = _base_resp()
        return SimulationResponse(
            voyage_id=voyage_id, origin=orig_id, destination=dest_id,
            spatially_relevant=False, old_route=old_coords, new_route=old_coords,
            reason=reason, eta_change_hours=0.0, fuel_change_mt=0.0,
            safety_change=0.0, congestion_change=0.0, rerouted=False,
            active_route=base_r,
            event_type=event.type, timestamp=start_time, severity=event.severity,
            eta_before=base_r.eta_hours if base_r else 0.0,
            eta_after=base_r.eta_hours if base_r else 0.0,
            fuel_before=base_r.fuel_mt if base_r else 0.0,
            fuel_after=base_r.fuel_mt if base_r else 0.0,
            safety_before=base_r.safety_score if base_r else 0.0,
            safety_after=base_r.safety_score if base_r else 0.0,
            cost_improvement_percent=0.0,
            hysteresis_threshold_percent=round(hysteresis * 100.0, 1),
            decision="SPATIALLY_IRRELEVANT",
            security_advisories=base_r.security_advisories if base_r else [],
            max_security_risk=base_r.max_security_risk if base_r else 0.0,
            intersected_security_zones=base_r.intersected_security_zones if base_r else [],
        )

    # 3. Handle Spatially Relevant Event (Port Congestion, Security, or Storm)
    if event.type == "port_congestion":
        added_wait_h     = round(event.severity * 18.0, 1)
        added_fuel_mt    = round(event.severity * 4.0, 1)
        congestion_delta = round(event.severity * 8.0, 1)
        safety_delta     = round(event.severity * 5.0, 1)

        base_r = _base_resp()
        congested_active_route = base_r.model_copy(update={
            "eta_hours":        round(base_r.eta_hours + added_wait_h, 1),
            "fuel_mt":          round(base_r.fuel_mt + added_fuel_mt, 1),
            "congestion_score": min(10.0, round(base_r.congestion_score + congestion_delta, 1)),
            "safety_score":     max(0.0,  round(base_r.safety_score - safety_delta, 1)),
            "reason": (
                f"{label} ({event.lat:.2f}°N, {event.lon:.2f}°E), "
                f"{min_dist_to_remaining_km:.0f} km from route. "
                f"Port wait +{added_wait_h}h, idle fuel +{added_fuel_mt} MT. "
                f"Congestion ↑{congestion_delta:.1f}, safety ↓{safety_delta:.1f}."
            ),
        })

        reason = (
            f"{label} detected {min_dist_to_remaining_km:.0f} km from remaining "
            f"{orig_name} → {dest_name} corridor. Port waiting time +{added_wait_h}h, idle fuel +{added_fuel_mt} MT. "
            f"Current route geometry maintained with updated ETA ({congested_active_route.eta_hours}h)."
        )
        return SimulationResponse(
            voyage_id=voyage_id, origin=orig_id, destination=dest_id,
            spatially_relevant=True, old_route=old_coords, new_route=old_coords,
            reason=reason, eta_change_hours=added_wait_h, fuel_change_mt=added_fuel_mt,
            safety_change=safety_delta, congestion_change=congestion_delta,
            rerouted=False, active_route=congested_active_route,
            event_type=event.type, timestamp=start_time, severity=event.severity,
            eta_before=base_r.eta_hours,
            eta_after=congested_active_route.eta_hours,
            fuel_before=base_r.fuel_mt,
            fuel_after=congested_active_route.fuel_mt,
            safety_before=base_r.safety_score,
            safety_after=congested_active_route.safety_score,
            cost_improvement_percent=0.0,
            hysteresis_threshold_percent=round(hysteresis * 100.0, 1),
            decision="PORT_CONGESTION_UPDATED",
            security_advisories=congested_active_route.security_advisories,
            max_security_risk=congested_active_route.max_security_risk,
            intersected_security_zones=congested_active_route.intersected_security_zones,
        )

    # 4. Dedicated Security Threat Disruption Handling
    if event.type == "security":
        from backend.app.services.security import assess_route_security
        sec_eval = assess_route_security(old_coords)
        
        # Calculate meaningful safety penalty based on severity (up to 30 pts reduction)
        safety_penalty = round(max(0.15, event.severity) * 25.0, 1)
        base_r = _base_resp()
        
        # Compile comprehensive security advisories
        advisories = list(sec_eval.get("advisories", []))
        threat_desc = (
            f"Security Threat Alert: {event.severity * 100:.0f}% risk incident reported at "
            f"({event.lat:.2f}°N, {event.lon:.2f}°E), {min_dist_to_remaining_km:.0f} km from vessel course."
        )
        advisories.insert(0, threat_desc)
        if event.severity >= 0.7:
            advisories.append("Transit through designated High Risk Area: Mandate BMP5 counter-piracy protocols & 24h armed/radar watch.")
        else:
            advisories.append("Security advisory: Heightened bridge watch, active AIS beaconing, and evasion readiness required.")

        secured_safety = max(0.0, round(base_r.safety_score - safety_penalty, 1))
        secured_risk = round(max(event.severity, sec_eval.get("max_risk_level", 0.0)), 2)
        
        secured_active_route = base_r.model_copy(update={
            "safety_score": secured_safety,
            "security_advisories": advisories,
            "max_security_risk": secured_risk,
            "intersected_security_zones": sec_eval.get("intersected_zones", []),
            "reason": (
                f"{label} ({event.lat:.2f}°N, {event.lon:.2f}°E) located {min_dist_to_remaining_km:.0f} km from corridor. "
                f"Safety score ↓{safety_penalty:.1f} pts ({secured_safety}%). Mandatory watch protocols active."
            ),
        })

        reason = (
            f"{label} ({event.lat:.2f}°N, {event.lon:.2f}°E) detected {min_dist_to_remaining_km:.0f} km from remaining "
            f"{orig_name} → {dest_name} corridor. Safety score degraded by {safety_penalty} pts to {secured_safety}%. "
            f"Active navigation corridor maintained under enhanced BMP5 maritime security protocol."
        )

        return SimulationResponse(
            voyage_id=voyage_id, origin=orig_id, destination=dest_id,
            spatially_relevant=True, old_route=old_coords, new_route=old_coords,
            reason=reason, eta_change_hours=0.0, fuel_change_mt=0.0,
            safety_change=-safety_penalty, congestion_change=0.0,
            rerouted=False, active_route=secured_active_route,
            event_type=event.type, timestamp=start_time, severity=event.severity,
            eta_before=base_r.eta_hours,
            eta_after=secured_active_route.eta_hours,
            fuel_before=base_r.fuel_mt,
            fuel_after=secured_active_route.fuel_mt,
            safety_before=base_r.safety_score,
            safety_after=secured_active_route.safety_score,
            cost_improvement_percent=0.0,
            hysteresis_threshold_percent=round(hysteresis * 100.0, 1),
            decision="SECURITY_ALERT",
            security_advisories=advisories,
            max_security_risk=secured_risk,
            intersected_security_zones=sec_eval.get("intersected_zones", []),
        )

    # 5. Storm Weather Perturbation Handling
    speed_k = 8.0
    dir_deg = 90.0
    disrupted_weather = resolve_weather_provider(data_mode, storm={
        "start_lat":     event.lat,
        "start_lon":     event.lon,
        "speed_knots":   speed_k,
        "direction_deg": dir_deg,
        "radius_nm":     event.radius_km / 1.852,
        "intensity_max": max(1.0, min(10.0, event.severity * 10.0)),
    })

    disrupted_route = time_dependent_astar(
        graph=graph, start_node_id=current_node_id, target_node_id=dest_id,
        start_time=start_time, strategy=strategy, ship=ship,
        weather_provider=disrupted_weather,
        start_lat=curr_lat, start_lon=curr_lon,
    )

    base_r = _base_resp()
    if not disrupted_route:
        return SimulationResponse(
            voyage_id=voyage_id, origin=orig_id, destination=dest_id,
            spatially_relevant=True, old_route=old_coords, new_route=old_coords,
            reason=f"No navigable route found around {label}.",
            eta_change_hours=0.0, fuel_change_mt=0.0, safety_change=0.0, congestion_change=0.0,
            rerouted=False, active_route=base_r,
            event_type=event.type, timestamp=start_time, severity=event.severity,
            eta_before=base_r.eta_hours if base_r else 0.0,
            eta_after=base_r.eta_hours if base_r else 0.0,
            fuel_before=base_r.fuel_mt if base_r else 0.0,
            fuel_after=base_r.fuel_mt if base_r else 0.0,
            safety_before=base_r.safety_score if base_r else 0.0,
            safety_after=base_r.safety_score if base_r else 0.0,
            cost_improvement_percent=0.0,
            hysteresis_threshold_percent=round(hysteresis * 100.0, 1),
            decision="NO_ROUTE_FOUND",
            security_advisories=base_r.security_advisories if base_r else [],
            max_security_risk=base_r.max_security_risk if base_r else 0.0,
            intersected_security_zones=base_r.intersected_security_zones if base_r else [],
        )

    # Extract coordinates & metrics
    new_coords = [[graph.get_node(s.node_id).latitude, graph.get_node(s.node_id).longitude]
                  for s in disrupted_route.path if graph.get_node(s.node_id)]
    
    old_time   = baseline_route.total_time
    new_time   = disrupted_route.total_time
    old_fuel   = baseline_route.total_fuel
    new_fuel   = disrupted_route.total_fuel
    old_safety = baseline_route.total_safety
    new_safety = disrupted_route.total_safety
    old_cost   = baseline_route.total_cost
    new_cost   = disrupted_route.total_cost

    eta_delta    = round(new_time - old_time, 1)
    fuel_delta   = round(new_fuel - old_fuel, 1)
    safety_delta = round((new_safety - old_safety) * 4.0, 1)

    cost_impr_pct = abs((old_cost - new_cost) / old_cost * 100.0) if old_cost > 0 else 0.0
    rerouted = (old_coords != new_coords) and (new_cost <= old_cost * (1.0 - hysteresis))

    # Persist updated active route & weather provider to backend voyage
    if disrupted_route and voyage:
        if voyage.current_segment_idx > 0 and len(voyage.active_route.path) > voyage.current_segment_idx:
            hist_steps = voyage.active_route.path[:voyage.current_segment_idx + 1]
            offset = hist_steps[-1].accumulated_cost
            alt_steps = (
                disrupted_route.path[1:]
                if (disrupted_route.path and disrupted_route.path[0].node_id == hist_steps[-1].node_id)
                else disrupted_route.path
            )
            stitched_steps = list(hist_steps)
            for s in alt_steps:
                cs = s.model_copy()
                cs.accumulated_cost += offset
                stitched_steps.append(cs)
            stitched_route = RoutingResult(
                path=stitched_steps,
                total_cost=offset + disrupted_route.total_cost,
                total_time=sum(s.segment_time for s in stitched_steps),
                total_fuel=sum(s.segment_fuel for s in stitched_steps),
                total_safety=sum(s.segment_safety for s in stitched_steps),
                total_congestion=sum(s.segment_congestion for s in stitched_steps),
                strategy_name=voyage.strategy.name,
            )
            voyage.active_route = stitched_route
        else:
            voyage.active_route = disrupted_route
        voyage.projected_remaining_costs = _build_projected_costs(disrupted_route)
        _voyage_providers_db[voyage.id] = disrupted_weather
        _voyages_db[voyage.id] = voyage

    disrupted_route_resp = _build_route_response_from_routing_result(
        disrupted_route, graph, strategy.name, data_mode
    )

    if rerouted:
        path_str = " → ".join([s.node_id for s in disrupted_route.path])
        decision_code = "REROUTE"
        reason = (
            f"{label} {min_dist_to_remaining_km:.0f} km from corridor. "
            f"A* rerouted vessel via {path_str} (total cost improved by {cost_impr_pct:.1f}% > {hysteresis*100:.0f}% hysteresis). "
            f"New ETA: {disrupted_route_resp.eta_hours}h."
        )
    elif eta_delta > 0 or fuel_delta > 0 or safety_delta != 0:
        decision_code = "ROUTE_RETAINED"
        reason = (
            f"{label} {min_dist_to_remaining_km:.0f} km from remaining corridor. "
            f"Travel time +{eta_delta}h, fuel +{fuel_delta} MT on active path. "
            f"Alternate route improvement ({cost_impr_pct:.1f}%) did not exceed {hysteresis*100:.0f}% hysteresis threshold. "
            f"Retaining route geometry with updated ETA ({disrupted_route_resp.eta_hours}h)."
        )
    else:
        decision_code = "NO_IMPACT"
        reason = (
            f"{label} detected near route corridor. "
            f"Active route remains optimal under {strategy.name} strategy. Route and metrics maintained."
        )

    return SimulationResponse(
        voyage_id=voyage_id, origin=orig_id, destination=dest_id,
        spatially_relevant=True, old_route=old_coords, new_route=new_coords,
        reason=reason, eta_change_hours=eta_delta, fuel_change_mt=fuel_delta,
        safety_change=safety_delta, congestion_change=0.0,
        rerouted=rerouted, active_route=disrupted_route_resp,
        event_type=event.type, timestamp=start_time, severity=event.severity,
        eta_before=base_r.eta_hours if base_r else 0.0,
        eta_after=disrupted_route_resp.eta_hours,
        fuel_before=base_r.fuel_mt if base_r else 0.0,
        fuel_after=disrupted_route_resp.fuel_mt,
        safety_before=base_r.safety_score if base_r else 0.0,
        safety_after=disrupted_route_resp.safety_score,
        cost_improvement_percent=round(cost_impr_pct, 1),
        hysteresis_threshold_percent=round(hysteresis * 100.0, 1),
        decision=decision_code,
        security_advisories=disrupted_route_resp.security_advisories,
        max_security_risk=disrupted_route_resp.max_security_risk,
        intersected_security_zones=disrupted_route_resp.intersected_security_zones,
    )

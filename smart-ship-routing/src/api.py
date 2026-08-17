import os
from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.models import load_graph, Graph
from src.weather import DeterministicWeatherEngine, BaseWeatherProvider
from src.optimizer import STRATEGIES, ShipConfig
from src.simulation import Voyage, initialize_voyage, advance_voyage_simulation
from src.router import RoutingResult

app = FastAPI(title="SIH 2026 Ship Routing Backend API", version="1.0.0")

# Global in-memory storage for the prototype
voyages_db: Dict[str, Voyage] = {}
weather_providers_db: Dict[str, BaseWeatherProvider] = {}

# Default path to graph file
GRAPH_FILEPATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "traffic.json")

# Request / Response Schemas
class StormConfig(BaseModel):
    start_lat: float = 6.0
    start_lon: float = 85.0
    speed_knots: float = 8.0
    direction_deg: float = 90.0  # Moves East
    radius_nm: float = 150.0
    intensity_max: float = 8.0

class VoyageInitRequest(BaseModel):
    start_node_id: str
    target_node_id: str
    start_time: float = 0.0
    strategy: str = "BALANCED"  # FASTEST, SAFEST, LEAST_CONGESTED, BALANCED
    base_speed_knots: float = 15.0
    base_fuel_rate: float = 1.0
    hysteresis_threshold: float = 0.05
    storm: StormConfig = Field(default_factory=StormConfig)

class VoyageInitResponse(BaseModel):
    voyage_id: str
    active_route: RoutingResult
    current_node_id: str
    current_lat: float
    current_lon: float
    is_completed: bool

class TickRequest(BaseModel):
    tick_duration: float = 1.0

class TickResponse(BaseModel):
    voyage_id: str
    current_time: float
    current_node_id: str
    current_lat: float
    current_lon: float
    is_completed: bool
    active_route_nodes: List[str]
    rerouted_in_tick: bool
    new_route_cost: Optional[float] = None

# Helper to get graph
def get_graph() -> Graph:
    if not os.path.exists(GRAPH_FILEPATH):
        raise HTTPException(
            status_code=500,
            detail=f"Graph data not found at {GRAPH_FILEPATH}. Please generate it first."
        )
    return load_graph(GRAPH_FILEPATH)

@app.post("/voyage/init", response_model=VoyageInitResponse)
def init_voyage(req: VoyageInitRequest):
    # 1. Load the graph
    graph = get_graph()
    
    # 2. Check strategy
    strategy_name = req.strategy.upper()
    if strategy_name not in STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy '{req.strategy}'. Must be one of {list(STRATEGIES.keys())}"
        )
    strategy = STRATEGIES[strategy_name]
    
    # 3. Build ship configuration
    ship = ShipConfig(
        base_speed_knots=req.base_speed_knots,
        base_fuel_rate=req.base_fuel_rate
    )
    
    # 4. Build weather engine
    weather_provider = DeterministicWeatherEngine(
        start_lat=req.storm.start_lat,
        start_lon=req.storm.start_lon,
        speed_knots=req.storm.speed_knots,
        direction_deg=req.storm.direction_deg,
        radius_nm=req.storm.radius_nm,
        intensity_max=req.storm.intensity_max
    )
    
    # 5. Initialize Voyage
    voyage = initialize_voyage(
        graph=graph,
        start_node_id=req.start_node_id,
        target_node_id=req.target_node_id,
        start_time=req.start_time,
        strategy=strategy,
        ship=ship,
        weather_provider=weather_provider,
        hysteresis_threshold=req.hysteresis_threshold
    )
    
    if not voyage:
        raise HTTPException(
            status_code=400,
            detail=f"Could not find a path from {req.start_node_id} to {req.target_node_id}."
        )
        
    # Store in-memory
    voyages_db[voyage.id] = voyage
    weather_providers_db[voyage.id] = weather_provider
    
    return VoyageInitResponse(
        voyage_id=voyage.id,
        active_route=voyage.active_route,
        current_node_id=voyage.current_node_id,
        current_lat=voyage.current_lat,
        current_lon=voyage.current_lon,
        is_completed=voyage.is_completed
    )

@app.post("/voyage/{voyage_id}/tick", response_model=TickResponse)
def tick_voyage(voyage_id: str, req: TickRequest):
    if voyage_id not in voyages_db:
        raise HTTPException(status_code=404, detail="Voyage not found.")
        
    voyage = voyages_db[voyage_id]
    weather_provider = weather_providers_db[voyage_id]
    graph = get_graph()
    
    # Record reroute events count before advancing
    reroutes_before = len(voyage.reroute_events)
    
    # Advance the simulation
    advance_voyage_simulation(voyage, graph, weather_provider, req.tick_duration)
    
    # Check if a reroute was triggered and actually succeeded (path changed)
    rerouted_in_tick = False
    new_cost = None
    if len(voyage.reroute_events) > reroutes_before:
        last_event = voyage.reroute_events[-1]
        rerouted_in_tick = last_event.route_changed
        if rerouted_in_tick:
            new_cost = voyage.active_route.total_cost

    return TickResponse(
        voyage_id=voyage.id,
        current_time=voyage.current_time,
        current_node_id=voyage.current_node_id,
        current_lat=voyage.current_lat,
        current_lon=voyage.current_lon,
        is_completed=voyage.is_completed,
        active_route_nodes=[step.node_id for step in voyage.active_route.path],
        rerouted_in_tick=rerouted_in_tick,
        new_route_cost=new_cost
    )

@app.get("/voyage/{voyage_id}/route", response_model=RoutingResult)
def get_voyage_route(voyage_id: str):
    if voyage_id not in voyages_db:
        raise HTTPException(status_code=404, detail="Voyage not found.")
    return voyages_db[voyage_id].active_route

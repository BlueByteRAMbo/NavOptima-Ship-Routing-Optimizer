"""
Route and Simulation Data Models
Pydantic schemas matching the frontend contract and project specification.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OptimizationPreferences(BaseModel):
    fuel_weight: Optional[float] = None
    time_weight: Optional[float] = None
    safety_weight: Optional[float] = None
    congestion_weight: Optional[float] = None


class RouteRequest(BaseModel):
    # Primary frontend properties
    origin: Optional[str] = None
    destination: Optional[str] = None
    ship: Optional[str] = "container"
    optimization: Optional[str] = "balanced"
    data_mode: Optional[str] = "HYBRID"  # 'MOCK' | 'HYBRID' | 'COPERNICUS'

    # API contract aliases
    origin_port: Optional[str] = None
    destination_port: Optional[str] = None
    ship_type: Optional[str] = None
    departure_time: Optional[str] = None
    optimization_preferences: Optional[OptimizationPreferences] = None

    def get_origin(self) -> str:
        return (self.origin or self.origin_port or "").strip()

    def get_destination(self) -> str:
        return (self.destination or self.destination_port or "").strip()

    def get_ship(self) -> str:
        return (self.ship or self.ship_type or "container").strip().lower()

    def get_optimization(self) -> str:
        if self.optimization:
            opt = self.optimization.strip().upper()
            if opt in ("FASTEST", "SAFEST", "LEAST_CONGESTED", "BALANCED"):
                return opt
            if opt == "FUEL_EFFICIENT":
                return "LEAST_CONGESTED"
        if self.optimization_preferences:
            pref = self.optimization_preferences
            tw = pref.time_weight or 0
            sw = pref.safety_weight or 0
            cw = pref.congestion_weight or 0
            if tw >= 0.7:
                return "FASTEST"
            if sw >= 0.7:
                return "SAFEST"
            if cw >= 0.5:
                return "LEAST_CONGESTED"
        return "BALANCED"


class RouteResponse(BaseModel):
    coordinates: List[List[float]]
    distance_km: float
    eta_hours: float
    fuel_mt: float
    safety_score: float
    congestion_score: Optional[float] = None
    total_cost: Optional[float] = None
    reason: str
    strategy: str = "BALANCED"
    data_mode: str = "HYBRID"
    data_status: str = "CACHED"
    routing_supported: bool = True
    path_nodes: Optional[List[str]] = None
    security_advisories: List[str] = Field(default_factory=list)
    max_security_risk: float = 0.0
    intersected_security_zones: List[Dict[str, Any]] = Field(default_factory=list)


class SimulationEvent(BaseModel):
    voyage_id: Optional[str] = None
    type: str  # 'storm' | 'port_congestion' | 'security'
    lat: float
    lon: float
    radius_km: float
    severity: float
    label: Optional[str] = None


class SimulationResponse(BaseModel):
    voyage_id: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    spatially_relevant: bool = True
    old_route: List[List[float]]
    new_route: List[List[float]]
    reason: str
    eta_change_hours: float
    fuel_change_mt: float
    safety_change: float
    congestion_change: float = 0.0
    rerouted: bool = True
    active_route: Optional[RouteResponse] = None

    # Structured Decision Log Fields (Phase 14 Section I)
    event_type: Optional[str] = None
    timestamp: Optional[float] = None
    severity: Optional[float] = None
    eta_before: Optional[float] = None
    eta_after: Optional[float] = None
    fuel_before: Optional[float] = None
    fuel_after: Optional[float] = None
    safety_before: Optional[float] = None
    safety_after: Optional[float] = None
    cost_improvement_percent: Optional[float] = None
    hysteresis_threshold_percent: Optional[float] = None
    decision: Optional[str] = None  # 'REROUTE' | 'ROUTE_RETAINED' | 'SPATIALLY_IRRELEVANT' | 'NO_IMPACT' | 'SECURITY_ALERT' | 'PORT_CONGESTION_UPDATED'
    security_advisories: List[str] = Field(default_factory=list)
    max_security_risk: float = 0.0
    intersected_security_zones: List[Dict[str, Any]] = Field(default_factory=list)


class VoyageCreateRequest(BaseModel):
    origin: str
    destination: str
    ship: str = "container"
    optimization: str = "BALANCED"
    data_mode: str = "HYBRID"
    hysteresis_threshold: float = 0.05
    storm: Optional[Dict[str, Any]] = None


class VoyageStateResponse(BaseModel):
    voyage_id: str
    origin: str
    destination: str
    ship: str
    strategy: str
    data_mode: str
    current_time: float
    current_lat: float
    current_lon: float
    current_node_id: str
    is_completed: bool
    active_route: RouteResponse
    history: List[Dict[str, Any]] = []
    reroute_events: List[Dict[str, Any]] = []


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
    active_route: RouteResponse
    rerouted_in_tick: bool
    new_route_cost: Optional[float] = None
    reroute_event: Optional[Dict[str, Any]] = None


class DataSource(BaseModel):
    source: str
    dataset: str
    region: str
    variables: List[str]
    status: str
    note: str
    retrieved_at: Optional[str] = None
    valid_time: Optional[str] = None

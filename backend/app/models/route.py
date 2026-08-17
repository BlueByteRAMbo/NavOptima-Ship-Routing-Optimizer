"""
Route and Simulation Data Models
Pydantic schemas matching the frontend contract and project specification.
"""
from typing import List, Optional
from pydantic import BaseModel


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
            return self.optimization.strip().lower()
        if self.optimization_preferences:
            pref = self.optimization_preferences
            fw = pref.fuel_weight or 0
            tw = pref.time_weight or 0
            sw = pref.safety_weight or 0
            if tw >= 0.7:
                return "fastest"
            if sw >= 0.7:
                return "safest"
            if fw >= 0.7:
                return "fuel_efficient"
        return "balanced"


class RouteResponse(BaseModel):
    coordinates: List[List[float]]
    distance_km: float
    eta_hours: float
    fuel_mt: float
    safety_score: float
    reason: str


class SimulationEvent(BaseModel):
    type: str  # 'storm' | 'port_congestion' | 'security'
    lat: float
    lon: float
    radius_km: float
    severity: float
    label: Optional[str] = None


class SimulationResponse(BaseModel):
    old_route: List[List[float]]
    new_route: List[List[float]]
    reason: str
    eta_change_hours: float
    fuel_change_mt: float
    safety_change: float


class DataSource(BaseModel):
    source: str
    dataset: str
    region: str
    variables: List[str]
    status: str
    note: str
    retrieved_at: Optional[str] = None
    valid_time: Optional[str] = None

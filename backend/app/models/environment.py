"""
EnvironmentCell Data Model
Schema matching Phase 9 Contract:
{
  "lat": float,
  "lon": float,
  "is_ocean": bool,
  "wind_speed": float,
  "wind_direction": float,
  "wave_height": float,
  "wave_period": float,
  "current_u": float,
  "current_v": float,
  "security_risk": float,
  "traffic_density": float,
  "timestamp": str,
  "sources": list,
  "data_status": dict
}
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class EnvironmentCell(BaseModel):
    lat: float
    lon: float
    is_ocean: bool = True
    wind_speed: float = 0.0
    wind_direction: float = 0.0
    wave_height: float = 0.0
    wave_period: float = 0.0
    current_u: float = 0.0
    current_v: float = 0.0
    security_risk: float = 0.0
    traffic_density: float = 0.0
    timestamp: str = ""
    sources: List[str] = Field(default_factory=list)
    data_status: Dict[str, Any] = Field(default_factory=dict)

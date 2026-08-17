"""
Port Data Model
Schema matching backend/data/cache/ports.json and frontend Port interface.
"""
from typing import Optional
from pydantic import BaseModel


class Port(BaseModel):
    id: str
    name: str
    country: str
    lat: float
    lon: float
    type: str = "seaport"
    congestion: float = 0.0
    waiting_hours: float = 0.0
    utilization: float = 0.0
    source: Optional[str] = None
    data_status: Optional[str] = "MOCK"
    timestamp: Optional[str] = None
    supported_in_routing: bool = True

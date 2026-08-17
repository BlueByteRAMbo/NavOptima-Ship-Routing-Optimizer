"""
Ship Profile Models
Vessel specifications, hydrodynamic profiles, and fuel consumption parameters.
"""
from typing import Dict
from pydantic import BaseModel


class ShipProfile(BaseModel):
    id: str
    name: str
    type: str
    speed_knots: float
    fuel_rate_mt_per_hour: float
    icon: str = "🚢"


DEFAULT_SHIPS: Dict[str, ShipProfile] = {
    "container": ShipProfile(
        id="container",
        name="Container Vessel",
        type="container",
        speed_knots=18.0,
        fuel_rate_mt_per_hour=2.1,
        icon="🚢",
    ),
    "bulk": ShipProfile(
        id="bulk",
        name="Bulk Carrier",
        type="bulk",
        speed_knots=14.0,
        fuel_rate_mt_per_hour=1.6,
        icon="🚧",
    ),
    "tanker": ShipProfile(
        id="tanker",
        name="Oil Tanker",
        type="tanker",
        speed_knots=15.0,
        fuel_rate_mt_per_hour=2.8,
        icon="🛢️",
    ),
    "lng": ShipProfile(
        id="lng",
        name="LNG Carrier",
        type="lng",
        speed_knots=19.0,
        fuel_rate_mt_per_hour=3.2,
        icon="⛽",
    ),
}

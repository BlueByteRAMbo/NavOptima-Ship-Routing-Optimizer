"""
Security Risk Service
Serves security threat levels, conflict zone boundaries, and risk zones
sourced from backend/data/cache/environment.json.
"""
from typing import Any, Dict, List, Optional
from backend.app.models.environment import EnvironmentCell
from backend.app.services.data_loader import get_environment_cells


def get_security_grid(
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    limit: Optional[int] = None,
) -> List[EnvironmentCell]:
    """Returns environment cells with security_risk indices."""
    return get_environment_cells(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        limit=limit,
    )


def get_security_zones() -> List[Dict[str, Any]]:
    """Returns curated security zones in the Indian Ocean."""
    return [
        {
            "id": "gulf_of_aden_hha",
            "name": "Gulf of Aden & Southern Red Sea High Risk Area",
            "center_lat": 12.5,
            "center_lon": 47.5,
            "radius_km": 250.0,
            "risk_level": 0.75,
            "threat_type": "Piracy / Regional Conflict",
            "source": "ACLED / Maritime Security Center",
            "status": "MOCK",
        },
        {
            "id": "strait_of_malacca_traffic_zone",
            "name": "Strait of Malacca Security & Traffic Watch Area",
            "center_lat": 2.5,
            "center_lon": 101.5,
            "radius_km": 120.0,
            "risk_level": 0.35,
            "threat_type": "Chokepoint / Dense Traffic",
            "source": "ReCAAP / Simulated",
            "status": "MOCK",
        },
    ]

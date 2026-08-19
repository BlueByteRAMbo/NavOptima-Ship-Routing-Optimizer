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


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in km."""
    import math
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def assess_route_security(coordinates: List[List[float]]) -> Dict[str, Any]:
    """
    Evaluates security risk and zone intersections along a route trajectory.
    Enforces real product rules (e.g. BMP5 counter-piracy and watch protocols).
    """
    zones = get_security_zones()
    intersected_zones = []
    max_risk = 0.0

    if not coordinates:
        return {
            "is_secure": True,
            "max_risk_level": 0.0,
            "intersected_zones": [],
            "advisories": [],
        }

    for zone in zones:
        z_lat = float(zone["center_lat"])
        z_lon = float(zone["center_lon"])
        z_rad = float(zone["radius_km"])
        z_risk = float(zone["risk_level"])

        for pt in coordinates:
            if len(pt) >= 2:
                dist = _haversine_km(pt[0], pt[1], z_lat, z_lon)
                if dist <= z_rad:
                    intersected_zones.append({
                        "zone_id": zone["id"],
                        "zone_name": zone["name"],
                        "threat_type": zone["threat_type"],
                        "risk_level": z_risk,
                        "distance_to_center_km": round(dist, 1),
                    })
                    if z_risk > max_risk:
                        max_risk = z_risk
                    break

    advisories: List[str] = []
    if max_risk >= 0.7:
        advisories.append("High Risk Area (HRA) transit detected: BMP5 counter-piracy measures, 24h armed/radar watch required.")
    elif max_risk >= 0.3:
        advisories.append("Heightened security watch recommended: maintain continuous AIS broadcast and radar lookout.")

    return {
        "is_secure": max_risk < 0.7,
        "max_risk_level": round(max_risk, 2),
        "intersected_zones": intersected_zones,
        "advisories": advisories,
    }

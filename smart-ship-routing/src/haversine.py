import math

EARTH_RADIUS_NM = 3440.065  # Earth radius in nautical miles (equivalent to ~6371 km)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface
    specified in decimal degrees (latitude and longitude).
    
    Returns the distance in nautical miles.
    """
    # Convert latitude and longitude from decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Difference in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.asin(math.sqrt(a))
    
    return EARTH_RADIUS_NM * c

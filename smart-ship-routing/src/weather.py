import math
from abc import ABC, abstractmethod
from src.haversine import haversine_distance, EARTH_RADIUS_NM

class BaseWeatherProvider(ABC):
    @abstractmethod
    def get_conditions(self, lat: float, lon: float, time_hours: float) -> float:
        """
        Get the weather conditions (specifically storm intensity on a scale of 0 to 10)
        at a specific location (lat, lon) and simulation time (in hours).
        """
        pass

class DeterministicWeatherEngine(BaseWeatherProvider):
    def __init__(self, start_lat: float, start_lon: float, speed_knots: float, 
                 direction_deg: float, radius_nm: float, intensity_max: float = 10.0):
        """
        Initialize a moving Gaussian storm.
        - start_lat, start_lon: Initial position of the storm center at time = 0.
        - speed_knots: Speed at which the storm is moving in knots (nautical miles per hour).
        - direction_deg: Direction/bearing of the storm movement in degrees (0 = North, 90 = East, etc.).
        - radius_nm: Spatial standard deviation (sigma) of the Gaussian storm in nautical miles.
        - intensity_max: Maximum intensity at the center of the storm (default 10.0).
        """
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.speed_knots = speed_knots
        self.direction_deg = direction_deg
        self.radius_nm = radius_nm
        self.intensity_max = intensity_max

    def get_storm_center(self, time_hours: float) -> tuple[float, float]:
        """
        Calculate the coordinates of the storm center at a given simulation time.
        Uses spherical great-circle navigation equations.
        """
        if time_hours <= 0:
            return self.start_lat, self.start_lon

        distance_traveled = self.speed_knots * time_hours
        
        # Spherical displacement calculations
        bearing_rad = math.radians(self.direction_deg)
        lat1_rad = math.radians(self.start_lat)
        lon1_rad = math.radians(self.start_lon)
        angular_dist = distance_traveled / EARTH_RADIUS_NM

        # Calculate new latitude in radians
        lat2_rad = math.asin(
            math.sin(lat1_rad) * math.cos(angular_dist) +
            math.cos(lat1_rad) * math.sin(angular_dist) * math.cos(bearing_rad)
        )

        # Calculate new longitude in radians
        lon2_rad = lon1_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(angular_dist) * math.cos(lat1_rad),
            math.cos(angular_dist) - math.sin(lat1_rad) * math.sin(lat2_rad)
        )

        # Convert back to degrees and normalize longitude to [-180, 180]
        lat2 = math.degrees(lat2_rad)
        lon2 = math.degrees(lon2_rad)
        lon2 = (lon2 + 180.0) % 360.0 - 180.0

        return lat2, lon2

    def get_conditions(self, lat: float, lon: float, time_hours: float) -> float:
        """
        Returns the storm intensity at (lat, lon) at the given time_hours.
        Scale of 0.0 (no storm) to intensity_max (center of storm).
        """
        # 1. Find the storm center at the queried time
        center_lat, center_lon = self.get_storm_center(time_hours)

        # 2. Compute Haversine distance from the query point to the storm center
        dist_to_center = haversine_distance(lat, lon, center_lat, center_lon)

        # 3. Calculate Gaussian intensity
        # I(d) = I_max * exp(-d^2 / (2 * radius^2))
        intensity = self.intensity_max * math.exp(-(dist_to_center ** 2) / (2.0 * (self.radius_nm ** 2)))
        
        return round(intensity, 4)

from typing import Dict
from pydantic import BaseModel

# Objective strategy weight definitions as specified
# FASTEST: time = 1.0, fuel = 0.0, safety = 0.0, congestion = 0.0
# SAFEST: time = 0.1, fuel = 0.1, safety = 0.8, congestion = 0.0
# LEAST_CONGESTED: time = 0.2, fuel = 0.1, safety = 0.1, congestion = 0.6
# BALANCED: time = 0.35, fuel = 0.25, safety = 0.25, congestion = 0.15

class OptimizationStrategy(BaseModel):
    name: str
    w_time: float
    w_fuel: float
    w_safety: float
    w_congestion: float

STRATEGIES: Dict[str, OptimizationStrategy] = {
    "FASTEST": OptimizationStrategy(name="FASTEST", w_time=1.0, w_fuel=0.0, w_safety=0.0, w_congestion=0.0),
    "SAFEST": OptimizationStrategy(name="SAFEST", w_time=0.1, w_fuel=0.1, w_safety=0.8, w_congestion=0.0),
    "LEAST_CONGESTED": OptimizationStrategy(name="LEAST_CONGESTED", w_time=0.2, w_fuel=0.1, w_safety=0.1, w_congestion=0.6),
    "BALANCED": OptimizationStrategy(name="BALANCED", w_time=0.35, w_fuel=0.25, w_safety=0.25, w_congestion=0.15)
}

# Deterministic and documented Normalization Constants
# These scale the edge-level parameters to a similar order of magnitude (~1.0 for a typical edge)
# so that the weighted sums operate on comparable bases.
N_TIME = 10.0          # Hours: typical edge traversal time (~150 nm at ~15 knots)
N_FUEL = 10.0          # Fuel units (tons): typical edge fuel usage at ~1.0 ton/hour
N_SAFETY = 1.0         # Safety units: standard base safety scale factor
N_CONGESTION = 30.0    # Congestion units: base_congestion * distance_nm (e.g. 0.2 * 150 nm)

class ShipConfig(BaseModel):
    base_speed_knots: float = 15.0  # Base ship speed in knots
    base_fuel_rate: float = 1.0     # Fuel consumption rate in tons/hour (under calm weather)

def calculate_weather_modifiers(storm_intensity: float) -> tuple[float, float, float]:
    """
    Given a storm intensity (0 to 10 scale), compute:
    1. speed_modifier (fraction of base speed, e.g. 0.2 to 1.0)
    2. fuel_modifier (consumption rate multiplier, e.g. 1.0 to 2.5)
    3. safety_penalty (added cost component, e.g. 0.0 to 10.0)
    
    A higher storm intensity reduces speed, increases fuel burn rate, and increases safety penalty.
    """
    # Clip intensity to [0.0, 10.0] for calculations
    clamped_intensity = max(0.0, min(10.0, storm_intensity))
    ratio = clamped_intensity / 10.0

    # Speed modifier: decreases linearly with intensity, down to a minimum of 20% speed
    speed_modifier = max(0.2, 1.0 - ratio * 0.8)

    # Fuel modifier: increases linearly, up to 250% of the base fuel consumption rate
    fuel_modifier = 1.0 + ratio * 1.5

    # Safety penalty: increases linearly, up to 10.0
    safety_penalty = ratio * 10.0

    return speed_modifier, fuel_modifier, safety_penalty

def calculate_edge_cost(
    distance_nm: float,
    base_congestion: float,
    storm_intensity: float,
    ship: ShipConfig,
    strategy: OptimizationStrategy
) -> tuple[float, float, float, float, float]:
    """
    Calculate the travel details and the total objective cost for traversing an edge.
    
    Returns:
      (total_weighted_cost, travel_time, fuel_consumed, safety_penalty, congestion_cost)
    """
    # 1. Apply weather effects
    speed_mod, fuel_mod, safety_penalty = calculate_weather_modifiers(storm_intensity)
    
    effective_speed = ship.base_speed_knots * speed_mod
    travel_time = distance_nm / effective_speed
    fuel_consumed = ship.base_fuel_rate * fuel_mod * travel_time
    congestion_cost = base_congestion * distance_nm

    # 2. Normalize components
    norm_time = travel_time / N_TIME
    norm_fuel = fuel_consumed / N_FUEL
    norm_safety = safety_penalty / N_SAFETY
    norm_congestion = congestion_cost / N_CONGESTION

    # 3. Weighted summation
    total_cost = (
        strategy.w_time * norm_time +
        strategy.w_fuel * norm_fuel +
        strategy.w_safety * norm_safety +
        strategy.w_congestion * norm_congestion
    )

    return total_cost, travel_time, fuel_consumed, safety_penalty, congestion_cost

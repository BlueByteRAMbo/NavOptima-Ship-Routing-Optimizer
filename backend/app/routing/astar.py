"""
A* Maritime Routing Algorithm
Re-exports the core frozen algorithm from smart-ship-routing.
"""
from backend.app.orchestration.optimizer_service import (
    time_dependent_astar,
    calculate_optimal_route,
)

__all__ = ["time_dependent_astar", "calculate_optimal_route"]

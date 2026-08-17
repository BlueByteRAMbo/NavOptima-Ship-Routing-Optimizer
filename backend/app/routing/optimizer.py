"""
Multi-Objective Optimization Module
Re-exports optimization strategies and functions from smart-ship-routing.
"""
from backend.app.orchestration.optimizer_service import (
    STRATEGIES,
    OptimizationStrategy,
    ShipConfig,
)

__all__ = ["STRATEGIES", "OptimizationStrategy", "ShipConfig"]

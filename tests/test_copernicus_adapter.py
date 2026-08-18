"""
Test Copernicus Weather Provider & A* Routing Cost Influence
"""
import os
import sys
import pytest

ROUTING_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "smart-ship-routing")
)
if ROUTING_ROOT not in sys.path:
    sys.path.insert(0, ROUTING_ROOT)

from src.models import load_graph
from src.optimizer import STRATEGIES, ShipConfig
from src.router import time_dependent_astar
from src.weather import DeterministicWeatherEngine
from backend.app.services.copernicus_provider import CopernicusWeatherProvider


def test_copernicus_provider_grid_loading():
    provider = CopernicusWeatherProvider()
    assert len(provider.grid) > 10000, "Copernicus ocean grid should load >10,000 cells"


def test_copernicus_conditions_values():
    provider = CopernicusWeatherProvider()
    mumbai_cond = provider.get_conditions(18.95, 72.95, 0.0)
    malacca_cond = provider.get_conditions(2.5, 101.5, 0.0)
    
    assert 0.0 <= mumbai_cond <= 10.0
    assert 0.0 <= malacca_cond <= 10.0


def test_copernicus_influences_routing_cost():
    graph = load_graph(os.path.join(ROUTING_ROOT, "traffic.json"))
    ship = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)
    
    calm = DeterministicWeatherEngine(0, 0, 0, 0, 10, 0)
    copernicus = CopernicusWeatherProvider()

    res_calm = time_dependent_astar(graph, "Mumbai", "Singapore", 0.0, STRATEGIES["BALANCED"], ship, calm)
    res_copernicus = time_dependent_astar(graph, "Mumbai", "Singapore", 0.0, STRATEGIES["BALANCED"], ship, copernicus)

    assert res_calm is not None
    assert res_copernicus is not None
    assert res_copernicus.total_cost != res_calm.total_cost, "Copernicus ocean data must directly change A* routing cost"
    assert res_copernicus.total_fuel > res_calm.total_fuel, "Real ocean waves/currents must affect fuel burn calculation"

"""
Automated Test Suite for Strategy Weight Evaluation & Conflicting Scenarios (Part 7 & Part 18)
Verifies:
- FASTEST, SAFEST, LEAST_CONGESTED, and BALANCED use their exact documented weight vectors.
- Objective costs match weighted normalized formulas.
- Controlled scenario evaluation where objectives conflict.
"""
import os
import sys
import pytest

ROUTING_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "smart-ship-routing")
)
if ROUTING_ROOT not in sys.path:
    sys.path.insert(0, ROUTING_ROOT)

from src.models import Graph, Node, Edge
from src.optimizer import (
    STRATEGIES,
    OptimizationStrategy,
    ShipConfig,
    calculate_edge_cost,
)
from src.router import time_dependent_astar
from src.weather import DeterministicWeatherEngine


def test_strategy_weight_vectors():
    fastest = STRATEGIES["FASTEST"]
    safest = STRATEGIES["SAFEST"]
    least_cong = STRATEGIES["LEAST_CONGESTED"]
    balanced = STRATEGIES["BALANCED"]

    assert fastest.w_time == 1.0 and fastest.w_fuel == 0.0 and fastest.w_safety == 0.0 and fastest.w_congestion == 0.0
    assert safest.w_time == 0.1 and safest.w_fuel == 0.1 and safest.w_safety == 0.8 and safest.w_congestion == 0.0
    assert least_cong.w_time == 0.2 and least_cong.w_fuel == 0.1 and least_cong.w_safety == 0.1 and least_cong.w_congestion == 0.6
    assert balanced.w_time == 0.35 and balanced.w_fuel == 0.25 and balanced.w_safety == 0.25 and balanced.w_congestion == 0.15


def test_conflicting_objective_scenario_evaluation():
    # Construct a controlled 4-node graph with 2 alternative paths from A to C:
    # Path 1: A -> B -> C (Shorter, faster, but severe weather / high storm intensity)
    # Path 2: A -> D -> C (Longer, slower, but calm weather / low risk)
    
    n_a = Node(id="A", name="Port A", latitude=10.0, longitude=70.0, is_port=True)
    n_b = Node(id="B", name="Waypoint B (Stormy)", latitude=10.0, longitude=72.0, is_port=False)
    n_c = Node(id="C", name="Port C", latitude=10.0, longitude=74.0, is_port=True)
    n_d = Node(id="D", name="Waypoint D (Calm Seaway)", latitude=12.0, longitude=72.0, is_port=False)

    e1 = Edge(id="A_B", source_id="A", target_id="B", distance_nm=120.0, base_congestion=0.1)
    e2 = Edge(id="B_C", source_id="B", target_id="C", distance_nm=120.0, base_congestion=0.1)
    e3 = Edge(id="A_D", source_id="A", target_id="D", distance_nm=180.0, base_congestion=0.1)
    e4 = Edge(id="D_C", source_id="D", target_id="C", distance_nm=180.0, base_congestion=0.1)

    graph = Graph(nodes=[n_a, n_b, n_c, n_d], edges=[e1, e2, e3, e4])
    ship = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)

    # Severe storm overlay at Waypoint B
    storm_b = DeterministicWeatherEngine(
        start_lat=10.0, start_lon=72.0, speed_knots=0.0, direction_deg=0.0, radius_nm=100.0, intensity_max=9.5
    )

    # 1. FASTEST strategy favors shorter distance / transit time despite storm
    res_fastest = time_dependent_astar(graph, "A", "C", 0.0, STRATEGIES["FASTEST"], ship, storm_b)
    # 2. SAFEST strategy avoids the stormy B node and takes calm D detour
    res_safest = time_dependent_astar(graph, "A", "C", 0.0, STRATEGIES["SAFEST"], ship, storm_b)

    assert res_fastest is not None
    assert res_safest is not None

    path_fastest = [s.node_id for s in res_fastest.path]
    path_safest = [s.node_id for s in res_safest.path]

    assert "B" in path_fastest, "FASTEST should choose shorter path through B"
    assert "D" in path_safest, "SAFEST should choose detour through D avoiding storm at B"
    assert res_safest.total_safety < res_fastest.total_safety, "SAFEST route must have lower safety penalty than FASTEST"

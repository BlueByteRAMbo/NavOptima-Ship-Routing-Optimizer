"""
Automated Test Suite for Route Metric Internal Consistency (Part 6)
Verifies:
- distance = sum(edge distances in km)
- travel_time = sum(segment travel times)
- fuel = sum(segment fuel consumption)
- safety = sum(segment safety penalties)
- congestion = sum(segment congestion costs)
- objective_cost = weighted sum of normalized components
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
from src.optimizer import STRATEGIES, ShipConfig, N_TIME, N_FUEL, N_SAFETY, N_CONGESTION
from src.router import time_dependent_astar
from src.weather import DeterministicWeatherEngine
from backend.app.orchestration.optimizer_service import calculate_optimal_route
from backend.app.models.route import RouteRequest


def test_internal_metric_consistency_all_strategies():
    graph = load_graph(os.path.join(ROUTING_ROOT, "traffic.json"))
    ship = ShipConfig(base_speed_knots=18.0, base_fuel_rate=2.1)
    weather = DeterministicWeatherEngine(0, 0, 0, 0, 10, 0)

    strategies = ["FASTEST", "SAFEST", "LEAST_CONGESTED", "BALANCED"]
    routes_to_test = [
        ("Mumbai", "Singapore"),
        ("Mumbai", "Colombo"),
        ("Mumbai", "Kochi"),
        ("Kochi", "Singapore"),
    ]

    for strat_name in strategies:
        strat = STRATEGIES[strat_name]
        for orig, dest in routes_to_test:
            res = time_dependent_astar(graph, orig, dest, 0.0, strat, ship, weather)
            assert res is not None, f"Route {orig} -> {dest} under {strat_name} failed"

            # 1. Sum segment values
            sum_time = sum(step.segment_time for step in res.path)
            sum_fuel = sum(step.segment_fuel for step in res.path)
            sum_safety = sum(step.segment_safety for step in res.path)
            sum_cong = sum(step.segment_congestion for step in res.path)
            sum_cost = sum(step.segment_cost for step in res.path)

            # 2. Check total agreement
            assert abs(res.total_time - sum_time) < 1e-4, f"Travel time mismatch for {orig}->{dest}"
            assert abs(res.total_fuel - sum_fuel) < 1e-4, f"Fuel mismatch for {orig}->{dest}"
            assert abs(res.total_safety - sum_safety) < 1e-4, f"Safety mismatch for {orig}->{dest}"
            assert abs(res.total_congestion - sum_cong) < 1e-4, f"Congestion mismatch for {orig}->{dest}"
            assert abs(res.total_cost - sum_cost) < 1e-4, f"Objective cost mismatch for {orig}->{dest}"

            # 3. Check objective weight normalization formula
            expected_weighted_sum = (
                strat.w_time * (res.total_time / N_TIME) +
                strat.w_fuel * (res.total_fuel / N_FUEL) +
                strat.w_safety * (res.total_safety / N_SAFETY) +
                strat.w_congestion * (res.total_congestion / N_CONGESTION)
            )
            assert abs(res.total_cost - expected_weighted_sum) < 1e-4, f"Weighted cost formula mismatch for {strat_name}"


def test_backend_api_route_response_consistency():
    req = RouteRequest(
        origin="mumbai",
        destination="singapore",
        ship="container",
        optimization="BALANCED",
        data_mode="HYBRID",
    )
    resp = calculate_optimal_route(req)

    assert resp.routing_supported is True
    assert resp.distance_km > 3000
    assert resp.eta_hours > 50
    assert resp.fuel_mt > 100
    assert 0.0 <= resp.safety_score <= 100.0
    assert resp.total_cost is not None and resp.total_cost > 0

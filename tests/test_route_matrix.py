"""
Automated Route Calculation Test Matrix (Part 14)
Tests:
Routes:
- Mumbai -> Singapore
- Mumbai -> Colombo
- Mumbai -> Kochi
- Kochi -> Singapore
- Colombo -> Singapore
- Chennai -> Singapore

Strategies:
- FASTEST
- SAFEST
- LEAST_CONGESTED
- BALANCED

Data Modes:
- MOCK
- HYBRID
"""
import pytest
from backend.app.orchestration.optimizer_service import calculate_optimal_route
from backend.app.models.route import RouteRequest

ROUTES = [
    ("mumbai", "singapore"),
    ("mumbai", "colombo"),
    ("mumbai", "kochi"),
    ("kochi", "singapore"),
    ("colombo", "singapore"),
    ("chennai", "singapore"),
]

STRATEGIES = ["FASTEST", "SAFEST", "LEAST_CONGESTED", "BALANCED"]
DATA_MODES = ["MOCK", "HYBRID"]


@pytest.mark.parametrize("orig,dest", ROUTES)
@pytest.mark.parametrize("strat", STRATEGIES)
@pytest.mark.parametrize("mode", DATA_MODES)
def test_route_matrix(orig, dest, strat, mode):
    req = RouteRequest(
        origin=orig,
        destination=dest,
        ship="container",
        optimization=strat,
        data_mode=mode,
    )
    resp = calculate_optimal_route(req)

    assert resp.routing_supported is True, f"Route {orig}->{dest} should be supported"
    assert len(resp.coordinates) >= 2
    assert resp.distance_km > 0
    assert resp.eta_hours > 0
    assert resp.fuel_mt > 0
    assert 0.0 <= resp.safety_score <= 100.0
    assert resp.strategy == strat
    assert resp.data_mode == mode

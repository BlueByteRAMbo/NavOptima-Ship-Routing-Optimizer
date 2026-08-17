"""
Route Optimization API Router
"""
from fastapi import APIRouter
from backend.app.models.route import RouteRequest, RouteResponse
from backend.app.orchestration.optimizer_service import calculate_optimal_route

router = APIRouter(tags=["Routing"])


@router.post("/route", response_model=RouteResponse)
def compute_route(req: RouteRequest) -> RouteResponse:
    """
    Computes optimal maritime route given origin, destination, vessel profile, and objective weights.
    """
    return calculate_optimal_route(req)

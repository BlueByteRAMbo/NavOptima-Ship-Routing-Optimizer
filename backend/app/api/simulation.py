"""
Simulation Event API Router
"""
from fastapi import APIRouter
from backend.app.models.route import SimulationEvent, SimulationResponse
from backend.app.orchestration.optimizer_service import handle_simulation_event

router = APIRouter(tags=["Simulation"])


@router.post("/simulation/event", response_model=SimulationResponse)
def trigger_simulation_event(event: SimulationEvent) -> SimulationResponse:
    """
    Injects dynamic real-time disruptions (e.g. storm development, piracy warning, port closure)
    for simulation and dynamic route recalculation.
    """
    return handle_simulation_event(event)

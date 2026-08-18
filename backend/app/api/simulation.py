"""
Simulation & Stateful Voyage API Router
"""
from fastapi import APIRouter, HTTPException, Path, Query
from backend.app.models.route import (
    SimulationEvent,
    SimulationResponse,
    VoyageCreateRequest,
    VoyageStateResponse,
    TickRequest,
    TickResponse,
    RouteResponse,
)
from backend.app.orchestration.optimizer_service import (
    handle_simulation_event,
    create_voyage,
    get_voyage,
    tick_voyage,
)

router = APIRouter(tags=["Simulation & Voyages"])


@router.post("/voyages", response_model=VoyageStateResponse)
def init_voyage_endpoint(req: VoyageCreateRequest) -> VoyageStateResponse:
    """Initializes a new stateful voyage simulation session."""
    try:
        return create_voyage(req)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/voyages/{voyage_id}", response_model=VoyageStateResponse)
def get_voyage_endpoint(voyage_id: str = Path(...)) -> VoyageStateResponse:
    """Fetches full state and telemetry of an active voyage."""
    try:
        return get_voyage(voyage_id)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/voyages/{voyage_id}/tick", response_model=TickResponse)
def tick_voyage_endpoint(
    req: TickRequest, voyage_id: str = Path(...)
) -> TickResponse:
    """Advances simulation clock and evaluates hysteresis-based rerouting."""
    try:
        return tick_voyage(voyage_id, req.tick_duration)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.get("/voyages/{voyage_id}/route", response_model=RouteResponse)
def get_voyage_route_endpoint(voyage_id: str = Path(...)) -> RouteResponse:
    """Fetches active route of a voyage."""
    try:
        state = get_voyage(voyage_id)
        return state.active_route
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/voyages/{voyage_id}/event", response_model=SimulationResponse)
def trigger_voyage_event_endpoint(
    event: SimulationEvent, voyage_id: str = Path(...)
) -> SimulationResponse:
    """Applies a dynamic disruption event to an active voyage."""
    event.voyage_id = voyage_id
    try:
        return handle_simulation_event(event)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/simulation/event", response_model=SimulationResponse)
def trigger_simulation_event(event: SimulationEvent) -> SimulationResponse:
    """
    Injects dynamic real-time disruptions (e.g. storm development, piracy warning)
    for simulation and dynamic route recalculation.
    """
    try:
        return handle_simulation_event(event)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))


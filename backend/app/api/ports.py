"""
Ports API Router
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from backend.app.models.port import Port
from backend.app.services.ports import get_all_ports, get_port_by_id

router = APIRouter(tags=["Ports"])


@router.get("/ports", response_model=List[Port])
def list_ports() -> List[Port]:
    """Returns all 15 supported strategic port locations and metadata."""
    return get_all_ports()


@router.get("/ports/{port_id}", response_model=Port)
def get_port(port_id: str) -> Port:
    """Returns details for a specific port."""
    port = get_port_by_id(port_id)
    if not port:
        raise HTTPException(status_code=404, detail=f"Port '{port_id}' not found.")
    return port

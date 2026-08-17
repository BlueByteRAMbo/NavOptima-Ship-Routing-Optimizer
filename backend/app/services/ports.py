"""
Port Service
Provides querying and lookup for canonical port data.
"""
from typing import List, Optional
from backend.app.models.port import Port
from backend.app.services.data_loader import get_ports


def get_all_ports() -> List[Port]:
    """Returns all 15 canonical Indian Ocean ports."""
    return get_ports()


def get_port_by_id(port_id: str) -> Optional[Port]:
    """Retrieves a single port by its ID or lowercase name."""
    norm_id = port_id.strip().lower()
    for port in get_ports():
        if port.id.lower() == norm_id or port.name.lower() == norm_id:
            return port
    return None

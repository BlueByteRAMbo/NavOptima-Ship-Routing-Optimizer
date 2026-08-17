"""
Data Sources API Router
"""
from typing import List
from fastapi import APIRouter
from backend.app.models.route import DataSource
from backend.app.services.data_loader import get_data_sources

router = APIRouter(tags=["Data Sources"])


@router.get("/data-sources", response_model=List[DataSource])
def list_data_sources() -> List[DataSource]:
    """Returns metadata and status for all active data feeds."""
    return get_data_sources()

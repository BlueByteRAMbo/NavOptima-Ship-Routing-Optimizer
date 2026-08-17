"""
Health API Router
"""
from fastapi import APIRouter
from typing import Dict

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=Dict[str, str])
def get_health() -> Dict[str, str]:
    """Verify backend service availability and status."""
    return {"status": "healthy", "version": "0.1.0"}

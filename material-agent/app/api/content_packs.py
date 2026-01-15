"""
Content Pack API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.curriculum_discovery import (
    CurriculumDiscoveryRequest,
    CurriculumDiscoveryResult,
)
from app.services.curriculum_discovery_service import CurriculumDiscoveryService
from app.database import get_database

router = APIRouter(prefix="/content-packs", tags=["content-packs"])


@router.post("/discover", response_model=CurriculumDiscoveryResult)
async def discover_curriculum(
    request: CurriculumDiscoveryRequest,
    db = Depends(get_database)
):
    """
    Trigger curriculum discovery (Job 1)
    
    This endpoint starts the autonomous discovery process:
    1. Discovers official curriculum documents
    2. Extracts topics and objectives
    3. Searches for OER sources
    4. Scores and vets sources
    5. Saves to database
    
    Returns:
        CurriculumDiscoveryResult with curriculum map or error
    """
    service = CurriculumDiscoveryService(db_connection=db, use_cloud=True)
    
    try:
        result = await service.discover_curriculum(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

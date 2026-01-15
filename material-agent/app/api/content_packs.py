"""
Content Pack API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.curriculum_discovery import (
    CurriculumDiscoveryRequest,
    CurriculumDiscoveryResult,
)
from app.schemas.content_extraction import (
    ContentExtractionRequest,
    ContentExtractionResult,
)
from app.services.curriculum_discovery_service import CurriculumDiscoveryService
from app.services.content_extraction_service import ContentExtractionService
from app.database import get_database
from config import settings

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


@router.post("/extract-content", response_model=ContentExtractionResult)
async def extract_content(
    request: ContentExtractionRequest,
    db = Depends(get_database)
):
    """
    Trigger content extraction (Job 2)
    
    This endpoint extracts content from vetted sources:
    1. Gets vetted sources from Job 1
    2. Extracts content (PDF, HTML, Video)
    3. Chunks content into teaching units
    4. Generates embeddings
    5. Saves knowledge chunks to database
    
    Returns:
        ContentExtractionResult with statistics
    """
    service = ContentExtractionService(
        db_connection=db,
        openai_api_key=settings.openai_api_key,
        use_cloud=True
    )
    
    try:
        result = await service.extract_content_from_sources(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
Content Pack API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
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


# Combined result schema
class FullPipelineResult(BaseModel):
    """Result from running both Job 1 and Job 2"""
    success: bool
    job1_result: CurriculumDiscoveryResult
    job2_result: Optional[ContentExtractionResult] = None
    error_message: Optional[str] = None


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


@router.post("/full-pipeline", response_model=FullPipelineResult)
async def run_full_pipeline(
    request: CurriculumDiscoveryRequest,
    max_sources: Optional[int] = 3,
    db = Depends(get_database)
):
    """
    Run the complete pipeline: Job 1 (Discovery) → Job 2 (Extraction)
    
    This endpoint runs both jobs sequentially:
    1. Discovers curriculum and OER sources (Job 1)
    2. Extracts content and creates knowledge chunks (Job 2)
    
    Args:
        request: Curriculum discovery parameters
        max_sources: Maximum sources to extract content from (default: 3)
    
    Returns:
        FullPipelineResult with results from both jobs
    """
    try:
        # Step 1: Run Job 1 (Discovery)
        discovery_service = CurriculumDiscoveryService(db_connection=db, use_cloud=True)
        job1_result = await discovery_service.discover_curriculum(request)
        
        if not job1_result.success:
            return FullPipelineResult(
                success=False,
                job1_result=job1_result,
                error_message=f"Job 1 failed: {job1_result.error_message}"
            )
        
        # Step 2: Run Job 2 (Extraction)
        curriculum_id = job1_result.curriculum_map.curriculum_id
        
        extraction_request = ContentExtractionRequest(
            curriculum_id=curriculum_id,
            max_sources=max_sources
        )
        
        extraction_service = ContentExtractionService(
            db_connection=db,
            openai_api_key=settings.openai_api_key,
            use_cloud=True
        )
        
        job2_result = await extraction_service.extract_content_from_sources(extraction_request)
        
        return FullPipelineResult(
            success=job2_result.success,
            job1_result=job1_result,
            job2_result=job2_result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


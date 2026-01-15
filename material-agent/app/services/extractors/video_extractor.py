"""
Video Content Extractor (DISABLED for cost optimization)
"""
import logging
from typing import Optional

from app.schemas.content_extraction import ExtractedContent
from app.services.extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class VideoExtractor(BaseExtractor):
    """
    Video transcript extractor - DISABLED
    
    Video transcripts are expensive to generate and process.
    This extractor is disabled to reduce costs.
    """
    
    def can_extract(self, url: str, content_format: str) -> bool:
        """
        OPTIMIZATION: Always return False to skip video extraction
        
        Videos are expensive to process:
        - Transcript generation costs money
        - Large text content increases embedding costs
        - Slower processing time
        """
        return False  # OPTIMIZED: Disabled video extraction
    
    async def extract(self, url: str, source_id: str) -> Optional[ExtractedContent]:
        """
        OPTIMIZATION: Video extraction disabled
        
        Args:
            url: Video URL
            source_id: Source ID
            
        Returns:
            None (extraction skipped)
        """
        logger.info(f"⏭️  Skipping video extraction for cost optimization: {url}")
        
        # OPTIMIZED: Return None to skip video processing entirely
        # Video transcripts are too expensive to generate and process
        
        return None

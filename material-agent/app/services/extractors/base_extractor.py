"""
Base extractor interface
"""
from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.content_extraction import ExtractedContent


class BaseExtractor(ABC):
    """Abstract base class for content extractors"""
    
    @abstractmethod
    async def extract(self, url: str, source_id: str) -> Optional[ExtractedContent]:
        """
        Extract content from URL
        
        Args:
            url: Source URL
            source_id: Source ID for tracking
            
        Returns:
            ExtractedContent or None if failed
        """
        pass
    
    @abstractmethod
    def can_extract(self, url: str, content_format: str) -> bool:
        """
        Check if this extractor can handle the given URL/format
        
        Args:
            url: Source URL
            content_format: Content format (PDF, HTML, etc.)
            
        Returns:
            True if can extract, False otherwise
        """
        pass

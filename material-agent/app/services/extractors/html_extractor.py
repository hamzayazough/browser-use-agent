"""
HTML Content Extractor using Browser-Use
"""
import logging
from typing import Optional
from urllib.parse import urlparse

from browser_use import Agent, Browser, ChatBrowserUse
from app.schemas.content_extraction import ExtractedContent, ContentFormat
from app.services.extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class HTMLExtractor(BaseExtractor):
    """Extract content from HTML pages using Browser-Use"""
    
    def __init__(self, use_cloud: bool = True):
        """
        Initialize HTML Extractor
        
        Args:
            use_cloud: Use Browser-Use cloud browser
        """
        self.use_cloud = use_cloud
        self.llm = ChatBrowserUse()
    
    def can_extract(self, url: str, content_format: str) -> bool:
        """Check if can extract from URL"""
        format_upper = content_format.upper()
        return format_upper in ["HTML", "URL", "INTERACTIVE", "UNKNOWN"]
    
    async def extract(self, url: str, source_id: str) -> Optional[ExtractedContent]:
        """
        Extract content from HTML page
        
        Args:
            url: Page URL
            source_id: Source ID
            
        Returns:
            ExtractedContent or None
        """
        try:
            logger.info(f"Extracting HTML from: {url}")
            
            # Configure browser
            browser = Browser(
                use_cloud=self.use_cloud,
                headless=True
            )
            
            # Create extraction task
            task = f"""
            Navigate to: {url}
            
            Extract the main educational content:
            1. Identify the main content area (skip navigation, ads, footers)
            2. Extract all text content including:
               - Headings and titles
               - Paragraphs and explanations
               - Examples and code snippets
               - Lists and bullet points
            3. Preserve the logical structure
            4. Note any images or diagrams (URLs)
            5. Return the content in a structured format
            6. Use 'done' action when complete
            """
            
            # Run agent
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=browser,
                use_vision=False
            )
            
            history = await agent.run(max_steps=30)
            
            # Extract result
            content_text = history.final_result() or ""
            
            if not content_text:
                logger.warning(f"No content extracted from {url}")
                return None
            
            # Count words
            word_count = len(content_text.split())
            
            # Detect language (simple heuristic)
            language = self._detect_language(content_text)
            
            extracted = ExtractedContent(
                source_id=source_id,
                raw_text=content_text,
                metadata={
                    "url": url,
                    "domain": urlparse(url).netloc
                },
                extraction_method="browser-use",
                word_count=word_count,
                language=language,
                has_visuals=False,  # TODO: Extract image URLs
                visual_urls=[]
            )
            
            logger.info(f"✅ Extracted {word_count} words from {url}")
            
            return extracted
            
        except Exception as e:
            logger.error(f"HTML extraction failed for {url}: {str(e)}")
            return None
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        # TODO: Use langdetect library for better detection
        # For now, assume English
        return "en"

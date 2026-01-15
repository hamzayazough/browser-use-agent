"""
PDF Content Extractor
"""
import logging
from typing import Optional
import io
import aiohttp

from app.schemas.content_extraction import ExtractedContent
from app.services.extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractor):
    """Extract content from PDF files"""
    
    def can_extract(self, url: str, content_format: str) -> bool:
        """Check if can extract from PDF"""
        return content_format.upper() == "PDF" or url.lower().endswith('.pdf')
    
    async def extract(self, url: str, source_id: str) -> Optional[ExtractedContent]:
        """
        Extract content from PDF
        
        Args:
            url: PDF URL
            source_id: Source ID
            
        Returns:
            ExtractedContent or None
        """
        try:
            logger.info(f"Extracting PDF from: {url}")
            
            # Download PDF
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download PDF: {response.status}")
                        return None
                    
                    pdf_bytes = await response.read()
            
            # Extract text using PyPDF2
            try:
                import PyPDF2
                
                pdf_file = io.BytesIO(pdf_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract all text
                text_parts = []
                total_pages = len(pdf_reader.pages)
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                
                raw_text = "\n\n".join(text_parts)
                
                # Get metadata
                metadata = {
                    "url": url,
                    "total_pages": total_pages,
                    "format": "PDF"
                }
                
                if pdf_reader.metadata:
                    metadata["title"] = pdf_reader.metadata.get("/Title", "")
                    metadata["author"] = pdf_reader.metadata.get("/Author", "")
                
                word_count = len(raw_text.split())
                
                extracted = ExtractedContent(
                    source_id=source_id,
                    raw_text=raw_text,
                    metadata=metadata,
                    extraction_method="pypdf2",
                    word_count=word_count,
                    language="en",  # TODO: Detect language
                    has_visuals=False
                )
                
                logger.info(f"✅ Extracted {word_count} words from {total_pages} pages")
                
                return extracted
                
            except ImportError:
                logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
                return None
            
        except Exception as e:
            logger.error(f"PDF extraction failed for {url}: {str(e)}")
            return None

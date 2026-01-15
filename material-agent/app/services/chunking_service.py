"""
Chunking Service - Split content into knowledge chunks
"""
import logging
import re
import uuid
from typing import List
from datetime import datetime

from app.schemas.content_extraction import (
    ExtractedContent,
    ContentChunk,
    ChunkType,
    ChunkingConfig
)

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for chunking content into teaching units"""
    
    def __init__(self, config: ChunkingConfig = None):
        """
        Initialize Chunking Service
        
        Args:
            config: Optional chunking configuration
        """
        self.config = config or ChunkingConfig()
    
    def chunk_content(
        self,
        extracted: ExtractedContent,
        topic_id: str,
        objective_ids: List[str]
    ) -> List[ContentChunk]:
        """
        Chunk extracted content into teaching units
        
        Args:
            extracted: Extracted content
            topic_id: Topic ID
            objective_ids: List of objective IDs
            
        Returns:
            List of content chunks
        """
        try:
            logger.info(f"Chunking content from source: {extracted.source_id}")
            
            # Split by strategy
            if self.config.split_by == "paragraph":
                chunks = self._chunk_by_paragraph(extracted.raw_text)
            elif self.config.split_by == "sentence":
                chunks = self._chunk_by_sentence(extracted.raw_text)
            else:
                chunks = self._chunk_by_paragraph(extracted.raw_text)
            
            # Filter by size
            chunks = [c for c in chunks if self._is_valid_chunk_size(c)]
            
            # Create ContentChunk objects
            content_chunks = []
            
            for i, chunk_text in enumerate(chunks):
                # Generate chunk ID
                chunk_id = f"ck_tpl_{uuid.uuid4().hex[:12]}"
                
                # Classify chunk type
                chunk_type = self._classify_chunk_type(chunk_text)
                
                # Assign objective (round-robin)
                objective_id = objective_ids[i % len(objective_ids)] if objective_ids else None
                
                # Estimate difficulty
                difficulty = self._estimate_difficulty(chunk_text)
                
                # Extract tags
                tags = self._extract_tags(chunk_text)
                
                content_chunk = ContentChunk(
                    chunk_id=chunk_id,
                    content=chunk_text.strip(),
                    chunk_type=chunk_type,
                    topic_id=topic_id,
                    objective_id=objective_id,
                    source_id=extracted.source_id,
                    word_count=len(chunk_text.split()),
                    difficulty=difficulty,
                    tags=tags,
                    skill_tags=[]
                )
                
                content_chunks.append(content_chunk)
            
            logger.info(f"✅ Created {len(content_chunks)} chunks")
            
            return content_chunks
            
        except Exception as e:
            logger.error(f"Chunking failed: {str(e)}")
            return []
    
    def _chunk_by_paragraph(self, text: str) -> List[str]:
        """Split text by paragraphs"""
        # Split by double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Clean empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Merge small paragraphs
        merged = []
        current = ""
        
        for para in paragraphs:
            word_count = len(para.split())
            
            if word_count >= self.config.min_chunk_size:
                if current:
                    merged.append(current)
                    current = ""
                merged.append(para)
            else:
                current += "\n\n" + para if current else para
                
                if len(current.split()) >= self.config.min_chunk_size:
                    merged.append(current)
                    current = ""
        
        if current:
            merged.append(current)
        
        # Split large paragraphs
        final_chunks = []
        for chunk in merged:
            if len(chunk.split()) > self.config.max_chunk_size:
                # Split into sentences
                sentences = re.split(r'[.!?]+', chunk)
                sub_chunk = ""
                
                for sent in sentences:
                    if len((sub_chunk + sent).split()) <= self.config.max_chunk_size:
                        sub_chunk += sent + ". "
                    else:
                        if sub_chunk:
                            final_chunks.append(sub_chunk.strip())
                        sub_chunk = sent + ". "
                
                if sub_chunk:
                    final_chunks.append(sub_chunk.strip())
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def _chunk_by_sentence(self, text: str) -> List[str]:
        """Split text by sentences"""
        # Split by sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Group sentences into chunks
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len((current_chunk + " " + sentence).split()) <= self.config.max_chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _is_valid_chunk_size(self, chunk: str) -> bool:
        """Check if chunk size is valid"""
        word_count = len(chunk.split())
        return self.config.min_chunk_size <= word_count <= self.config.max_chunk_size
    
    def _classify_chunk_type(self, text: str) -> ChunkType:
        """
        Classify chunk type based on content patterns
        
        Simple heuristic classification:
        - Definitions: Contains "is defined as", "means", "refers to"
        - Examples: Contains "for example", "such as", "instance"
        - Steps: Contains numbered lists, "first", "next", "then"
        - Tips: Contains "tip", "hint", "remember"
        """
        text_lower = text.lower()
        
        # Definition patterns
        if any(phrase in text_lower for phrase in ["is defined as", "definition", "means that", "refers to"]):
            return ChunkType.DEFINITION
        
        # Example patterns
        if any(phrase in text_lower for phrase in ["for example", "for instance", "such as", "e.g."]):
            return ChunkType.EXAMPLE
        
        # Step-by-step patterns
        if any(phrase in text_lower for phrase in ["first", "second", "step", "next", "then", "finally"]):
            if re.search(r'\d+\.', text):  # Has numbered list
                return ChunkType.STEP_BY_STEP
        
        # Tip patterns
        if any(phrase in text_lower for phrase in ["tip:", "hint:", "remember:", "note:"]):
            return ChunkType.TIP
        
        # Common mistake patterns
        if any(phrase in text_lower for phrase in ["common mistake", "avoid", "don't", "incorrect"]):
            return ChunkType.COMMON_MISTAKE
        
        # Analogy patterns
        if any(phrase in text_lower for phrase in ["like", "similar to", "imagine", "think of"]):
            return ChunkType.ANALOGY
        
        # Default: Concept explanation
        return ChunkType.CONCEPT_EXPLANATION
    
    def _estimate_difficulty(self, text: str) -> str:
        """
        Estimate difficulty based on text complexity
        
        Simple heuristic:
        - Easy: Short sentences, simple words
        - Medium: Moderate length, some technical terms
        - Hard: Long sentences, complex vocabulary
        """
        words = text.split()
        word_count = len(words)
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        # Sentence count
        sentence_count = len(re.split(r'[.!?]+', text))
        
        # Average sentence length
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Score
        complexity_score = (avg_word_length * 2) + (avg_sentence_length / 5)
        
        if complexity_score < 15:
            return "easy"
        elif complexity_score < 25:
            return "medium"
        else:
            return "hard"
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from content"""
        # TODO: Implement better tag extraction (NLP, keyword extraction)
        # For now, return empty list
        return []

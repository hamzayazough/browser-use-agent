"""
Pydantic models for Content Extraction Service
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# Input Schemas
# ============================================

class ContentExtractionRequest(BaseModel):
    """Input for content extraction"""
    curriculum_id: str = Field(..., description="Curriculum ID from Job 1")
    source_ids: Optional[List[str]] = Field(None, description="Specific sources to extract (optional)")
    max_sources: Optional[int] = Field(None, description="Limit number of sources")


class SourceExtractionTask(BaseModel):
    """Task for extracting from a single source"""
    source_id: str
    url: str
    content_format: str  # PDF, HTML, VIDEO, etc.
    topic_ids: List[str]
    objective_ids: List[str]


# ============================================
# Content Format Enum
# ============================================

class ContentFormat(str, Enum):
    """Content format types"""
    PDF = "PDF"
    HTML = "HTML"
    VIDEO = "VIDEO"
    TEXT = "TEXT"
    INTERACTIVE = "INTERACTIVE"
    UNKNOWN = "UNKNOWN"


# ============================================
# Extracted Content Schemas
# ============================================

class ExtractedContent(BaseModel):
    """Raw content extracted from source"""
    source_id: str
    raw_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_method: str  # "pdf", "html", "browser-use", etc.
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    word_count: int = 0
    language: Optional[str] = None
    has_visuals: bool = False
    visual_urls: List[str] = Field(default_factory=list)


# ============================================
# Chunking Schemas
# ============================================

class ChunkType(str, Enum):
    """Type of knowledge chunk"""
    CONCEPT_EXPLANATION = "CONCEPT_EXPLANATION"
    EXAMPLE = "EXAMPLE"
    STEP_BY_STEP = "STEP_BY_STEP"
    VISUAL_DIAGRAM = "VISUAL_DIAGRAM"
    ANALOGY = "ANALOGY"
    COMMON_MISTAKE = "COMMON_MISTAKE"
    TIP = "TIP"
    DEFINITION = "DEFINITION"


class ChunkScope(str, Enum):
    """Chunk scope"""
    TEMPLATE = "TEMPLATE"  # Shared across all instances
    INSTANCE = "INSTANCE"  # Private to specific roadmap instance


class ContentChunk(BaseModel):
    """A chunk of content before embedding"""
    chunk_id: str
    content: str
    chunk_type: ChunkType
    topic_id: str
    objective_id: Optional[str] = None
    source_id: str
    word_count: int = 0
    difficulty: Optional[str] = None  # easy, medium, hard
    tags: List[str] = Field(default_factory=list)
    skill_tags: List[str] = Field(default_factory=list)


class KnowledgeChunkWithEmbedding(BaseModel):
    """Complete knowledge chunk with embedding"""
    chunk_id: str
    scope: ChunkScope = ChunkScope.TEMPLATE
    topic_id: str
    objective_id: Optional[str] = None
    chunk_type: ChunkType
    content: str
    embedding: List[float] = Field(..., description="1536-dim vector")
    tags: List[str] = Field(default_factory=list)
    skill_tags: List[str] = Field(default_factory=list)
    difficulty: Optional[str] = None
    grade_level: Optional[str] = None
    source: Dict[str, Any]  # SourceAttribution
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# Output Schemas
# ============================================

class SourceExtractionResult(BaseModel):
    """Result of extracting from one source"""
    source_id: str
    success: bool
    chunks_created: int = 0
    error_message: Optional[str] = None
    extraction_time_seconds: float = 0


class ContentExtractionResult(BaseModel):
    """Result of content extraction job"""
    success: bool
    curriculum_id: str
    sources_processed: int = 0
    sources_successful: int = 0
    total_chunks_created: int = 0
    embeddings_generated: int = 0
    duration_seconds: float = 0
    extraction_results: List[SourceExtractionResult] = Field(default_factory=list)
    error_message: Optional[str] = None


# ============================================
# Chunking Configuration
# ============================================

class ChunkingConfig(BaseModel):
    """Configuration for content chunking"""
    min_chunk_size: int = Field(default=100, description="Minimum words per chunk")
    max_chunk_size: int = Field(default=500, description="Maximum words per chunk")
    overlap_size: int = Field(default=50, description="Overlap between chunks (words)")
    split_by: str = Field(default="paragraph", description="paragraph, sentence, semantic")
    preserve_structure: bool = Field(default=True, description="Maintain document structure")


# ============================================
# Embedding Configuration
# ============================================

class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation"""
    model: str = Field(default="text-embedding-3-small")
    dimensions: int = Field(default=1536)
    batch_size: int = Field(default=100, description="Batch size for API calls")
    max_retries: int = Field(default=3)
    retry_delay: float = Field(default=1.0)

"""
Knowledge Chunk MongoDB models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

from .base import PyObjectId


class ChunkScope(str, Enum):
    TEMPLATE = "TEMPLATE"
    INSTANCE = "INSTANCE"


class ChunkType(str, Enum):
    CONCEPT_EXPLANATION = "CONCEPT_EXPLANATION"
    EXAMPLE = "EXAMPLE"
    STEP_BY_STEP = "STEP_BY_STEP"
    VISUAL_DIAGRAM = "VISUAL_DIAGRAM"
    ANALOGY = "ANALOGY"
    COMMON_MISTAKE = "COMMON_MISTAKE"
    TIP = "TIP"
    DEFINITION = "DEFINITION"


class SourceAttribution(BaseModel):
    source_type: str
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None
    extracted_at: datetime


class KnowledgeChunkModel(BaseModel):
    """MongoDB document model for knowledge chunks"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    chunk_id: str
    scope: ChunkScope
    template_chunk_id: Optional[str] = None
    instance_id: Optional[str] = None
    topic_id: str
    objective_id: Optional[str] = None
    chunk_type: ChunkType
    content: str
    visual_url: Optional[str] = None
    embedding: Optional[List[float]] = None
    tags: List[str] = Field(default_factory=list)
    skill_tags: List[str] = Field(default_factory=list)
    difficulty: Optional[str] = None
    grade_level: Optional[str] = None
    related_chunk_ids: List[str] = Field(default_factory=list)
    source: SourceAttribution
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted: bool = False

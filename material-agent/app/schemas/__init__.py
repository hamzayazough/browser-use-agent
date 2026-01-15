"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Import curriculum discovery schemas
from .curriculum_discovery import *
from .source_scoring import *
from .content_extraction import *
from datetime import datetime
from enum import Enum


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
    source_type: str = Field(..., description="PDF, URL, OER, MANUAL, AI_GENERATED")
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None
    extracted_at: datetime


class KnowledgeChunkCreate(BaseModel):
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


class KnowledgeChunkResponse(KnowledgeChunkCreate):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    deleted: bool = False

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "chunk_id": "ck_tpl_greet_001",
                "scope": "TEMPLATE",
                "topic_id": "t1_greetings",
                "chunk_type": "CONCEPT_EXPLANATION",
                "content": "Buenos días is used from sunrise until noon...",
                "tags": ["greetings", "vocabulary"],
                "source": {
                    "source_type": "OER",
                    "source_name": "Khan Academy",
                    "license": "CC-BY-NC-SA 3.0",
                    "extracted_at": "2026-01-14T12:00:00Z"
                }
            }
        }


class CurriculumDiscoveryRequest(BaseModel):
    country: str = Field(..., min_length=2, max_length=2, description="2-letter country code")
    region: Optional[str] = Field(None, description="Region/province/state code")
    grade: str = Field(..., description="Grade level")
    subject: str = Field(..., description="Subject to learn")
    language: str = Field(default="en", description="Learning language preference")

    class Config:
        json_schema_extra = {
            "example": {
                "country": "CA",
                "region": "QC",
                "grade": "4",
                "subject": "Spanish",
                "language": "fr-CA"
            }
        }


class CurriculumDiscoveryResponse(BaseModel):
    job_id: str
    status: str = "QUEUED"
    message: str = "Curriculum discovery job has been queued"


class MaterialType(str, Enum):
    PDF = "PDF"
    IMAGE = "IMAGE"
    URL = "URL"
    VIDEO = "VIDEO"
    TEXT = "TEXT"


class MaterialStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MaterialCreate(BaseModel):
    material_id: str
    parent_id: str
    instance_id: Optional[str] = None
    template_id: Optional[str] = None
    material_type: MaterialType
    name: str
    description: Optional[str] = None
    source_url: Optional[str] = None


class MaterialResponse(MaterialCreate):
    id: str = Field(alias="_id")
    status: MaterialStatus
    created_at: datetime
    updated_at: datetime
    deleted: bool = False

    class Config:
        populate_by_name = True

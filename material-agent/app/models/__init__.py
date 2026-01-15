"""
MongoDB document models using Motor
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PyObjectId(str):
    """Custom ObjectId type for Pydantic models"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        from bson import ObjectId
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return str(v)


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
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    chunk_id: str = Field(..., unique=True)
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

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str}


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


class MaterialModel(BaseModel):
    """MongoDB document model for materials"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    material_id: str = Field(..., unique=True)
    parent_id: str
    instance_id: Optional[str] = None
    template_id: Optional[str] = None
    material_type: MaterialType
    name: str
    description: Optional[str] = None
    source_url: Optional[str] = None
    status: MaterialStatus = MaterialStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted: bool = False

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str}


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobType(str, Enum):
    CURRICULUM_DISCOVERY = "CURRICULUM_DISCOVERY"
    CONTENT_EXTRACTION = "CONTENT_EXTRACTION"
    VALIDATION = "VALIDATION"
    PUBLISH = "PUBLISH"


class JobModel(BaseModel):
    """MongoDB document model for background jobs"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    job_id: str = Field(..., unique=True)
    job_type: JobType
    status: JobStatus = JobStatus.QUEUED
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    progress: int = 0  # 0-100
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str}


class ContentPackModel(BaseModel):
    """MongoDB document model for published content packs"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    pack_id: str = Field(..., unique=True)
    country: str
    region: Optional[str] = None
    grade: str
    subject: str
    language: str
    curriculum_map: Dict[str, Any]
    chunk_ids_by_topic: Dict[str, List[str]]
    statistics: Dict[str, Any]
    deployment: Dict[str, Any]
    published_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "v1"
    status: str = "PUBLISHED"

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str}

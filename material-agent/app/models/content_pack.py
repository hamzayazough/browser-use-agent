"""
Content Pack MongoDB models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from .base import PyObjectId


class PackType(str, Enum):
    TEMPLATE = "TEMPLATE"
    INSTANCE = "INSTANCE"


class PackStatus(str, Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class ApprovalStatus(str, Enum):
    AUTO_APPROVED = "AUTO_APPROVED"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AuthorityLevel(str, Enum):
    OFFICIAL_GOVERNMENT = "OFFICIAL_GOVERNMENT"
    UNIVERSITY = "UNIVERSITY"
    EDUCATIONAL_NGO = "EDUCATIONAL_NGO"
    COMMUNITY = "COMMUNITY"


class Jurisdiction(BaseModel):
    country: str
    region: Optional[str] = None


class PackMetadata(BaseModel):
    jurisdiction: Jurisdiction
    grade: str
    subject: str
    language: str = "en"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    approval_status: ApprovalStatus = ApprovalStatus.PENDING_REVIEW
    human_review_required: bool = False
    tags: List[str] = Field(default_factory=list)
    estimated_completion_hours: Optional[float] = None
    difficulty_level: Optional[str] = None


class OfficialSourceDocument(BaseModel):
    url: str
    title: str
    publisher: str
    authority_level: AuthorityLevel


class CurriculumInfo(BaseModel):
    curriculum_id: str
    official_source_documents: List[OfficialSourceDocument]
    topic_count: int
    objective_count: int
    total_vocabulary_items: Optional[int] = None


class MaterialSource(BaseModel):
    source_id: str
    url: str
    title: str
    publisher: str
    license: str
    license_url: str
    authority_tier: int = Field(ge=0, le=5)
    total_score: int = Field(ge=0)
    chunk_count: int = Field(ge=0)


class PackStatistics(BaseModel):
    total_topics: int
    total_objectives: int
    total_sources: int
    total_chunks: int
    average_chunks_per_topic: float
    average_sources_per_topic: float
    total_vocabulary_words: Optional[int] = None
    estimated_study_time_minutes: Optional[int] = None
    license_diversity: Optional[Dict[str, int]] = None
    publisher_diversity: Optional[Dict[str, int]] = None


class QualityAssurance(BaseModel):
    validation_passed: bool = False
    coverage_score: float = Field(ge=0, le=1)
    license_compliance_score: float = Field(ge=0, le=1)
    source_quality_score: float = Field(ge=0, le=1)
    content_diversity_score: float = Field(ge=0, le=1)
    ready_for_production: bool = False
    last_validated_at: datetime = Field(default_factory=datetime.utcnow)


class Deployment(BaseModel):
    storage_location: Optional[str] = None
    cdn_url: Optional[str] = None
    vector_db_indexed: bool = False
    embeddings_generated: bool = False
    rag_searchable: bool = False
    last_indexed_at: Optional[datetime] = None


class UsageGuidelines(BaseModel):
    recommended_session_duration: Optional[int] = None
    recommended_sessions_per_week: Optional[int] = None
    total_weeks_to_complete: Optional[int] = None
    prerequisite_skills: List[str] = Field(default_factory=list)
    learning_outcomes: List[str] = Field(default_factory=list)
    assessment_types: List[str] = Field(default_factory=list)


class SessionPlan(BaseModel):
    session_number: int
    topic_id: str
    title: str
    duration_minutes: int
    chunk_ids: List[str]
    objectives: List[str]
    activities: List[str] = Field(default_factory=list)


class RoadmapTemplateInfo(BaseModel):
    template_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    session_count: int
    sessions: List[SessionPlan]


class ContentPackModel(BaseModel):
    """MongoDB document model for published content packs"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    pack_id: str
    pack_type: PackType
    status: PackStatus = PackStatus.DRAFT
    version: str = "1.0.0"
    curriculum_id: str
    metadata: PackMetadata
    curriculum: CurriculumInfo
    materials_by_topic: Dict[str, List[MaterialSource]]
    chunk_ids_by_topic: Dict[str, List[str]]
    statistics: PackStatistics
    quality_assurance: QualityAssurance
    deployment: Deployment = Field(default_factory=Deployment)
    usage_guidelines: Optional[UsageGuidelines] = None
    roadmap_template: Optional[RoadmapTemplateInfo] = None
    published_at: Optional[datetime] = None
    published_by: Optional[str] = None
    job_id: Optional[str] = None
    notes: List[str] = Field(default_factory=list)
    deleted: bool = False

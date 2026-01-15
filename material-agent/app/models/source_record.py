"""
Source Record MongoDB models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

from .base import PyObjectId


class SourceType(str, Enum):
    OFFICIAL_CURRICULUM = "OFFICIAL_CURRICULUM"
    UNIVERSITY_OER = "UNIVERSITY_OER"
    EDUCATIONAL_PLATFORM = "EDUCATIONAL_PLATFORM"
    GOVERNMENT_RESOURCE = "GOVERNMENT_RESOURCE"
    NGO_CONTENT = "NGO_CONTENT"
    COMMUNITY_CONTENT = "COMMUNITY_CONTENT"


class LicenseType(str, Enum):
    CC_BY = "CC-BY"
    CC_BY_SA = "CC-BY-SA"
    CC_BY_NC = "CC-BY-NC"
    CC_BY_NC_SA = "CC-BY-NC-SA"
    CC_BY_ND = "CC-BY-ND"
    CC_BY_NC_ND = "CC-BY-NC-ND"
    PUBLIC_DOMAIN = "PUBLIC-DOMAIN"
    CC0 = "CC0"
    CUSTOM_OER = "CUSTOM_OER"
    PROPRIETARY = "PROPRIETARY"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class ScoringBreakdown(BaseModel):
    authority: int = Field(ge=0, le=5)
    alignment: int = Field(ge=0, le=5)
    license: int = Field(ge=0, le=5)
    extractability: int = Field(ge=0, le=3)
    total: int = Field(ge=0)
    notes: Optional[str] = None


class ContentMetadata(BaseModel):
    language: Optional[str] = None
    format: Optional[str] = None
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    has_visuals: Optional[bool] = None
    has_interactive_elements: Optional[bool] = None
    estimated_reading_time_minutes: Optional[int] = None
    grade_level: Optional[str] = None
    topics_covered: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class VerificationInfo(BaseModel):
    status: VerificationStatus = VerificationStatus.PENDING
    last_verified_at: datetime = Field(default_factory=datetime.utcnow)
    verified_by: Optional[str] = None
    next_verification_due: Optional[datetime] = None
    verification_errors: List[str] = Field(default_factory=list)
    http_status_code: Optional[int] = None
    content_hash: Optional[str] = None


class ExtractionMetrics(BaseModel):
    chunks_created: int = 0
    last_extracted_at: Optional[datetime] = None
    extraction_job_id: Optional[str] = None
    extraction_successful: bool = True
    extraction_error: Optional[str] = None


class SourceRecordModel(BaseModel):
    """MongoDB document model for source records"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    source_id: str
    curriculum_id: str
    source_type: SourceType
    url: str
    title: str
    publisher: str
    author: Optional[str] = None
    license: LicenseType
    license_url: str
    scoring: ScoringBreakdown
    content_metadata: Optional[ContentMetadata] = None
    verification: VerificationInfo = Field(default_factory=VerificationInfo)
    extraction: Optional[ExtractionMetrics] = None
    topic_ids: List[str] = Field(default_factory=list)
    objective_ids: List[str] = Field(default_factory=list)
    created_chunk_ids: List[str] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    discovered_by: Optional[str] = None
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    deleted: bool = False

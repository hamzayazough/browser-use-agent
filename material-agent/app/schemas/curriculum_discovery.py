"""
Pydantic models for Curriculum Discovery Service
Defines input/output schemas and structured data formats
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# Input Schemas
# ============================================

class CurriculumDiscoveryRequest(BaseModel):
    """Input for curriculum discovery"""
    country: str = Field(..., description="2-letter country code (e.g., 'CA', 'US')")
    region: Optional[str] = Field(None, description="State/province code (e.g., 'QC', 'CA')")
    grade: str = Field(..., description="Grade level (e.g., '4', 'K', '10-12')")
    subject: str = Field(..., description="Subject (e.g., 'Spanish', 'Mathematics')")
    language: str = Field(default="en", description="Language code (e.g., 'en', 'fr-CA')")


# ============================================
# Official Document Schemas
# ============================================

class AuthorityLevel(str, Enum):
    """Authority level of curriculum sources"""
    OFFICIAL_GOVERNMENT = "OFFICIAL_GOVERNMENT"  # Ministry of Education
    UNIVERSITY = "UNIVERSITY"                     # University-published
    EDUCATIONAL_NGO = "EDUCATIONAL_NGO"          # Non-profit education org
    COMMUNITY = "COMMUNITY"                       # Community-created


class OfficialDocument(BaseModel):
    """Official curriculum document"""
    url: HttpUrl
    title: str
    publisher: str
    authority_level: AuthorityLevel
    publication_date: Optional[str] = None
    pdf_url: Optional[HttpUrl] = None


# ============================================
# Curriculum Structure Schemas
# ============================================

class LearningObjective(BaseModel):
    """A single learning objective"""
    objective_id: str = Field(..., description="Unique ID (e.g., 'obj_spanish_greet_001')")
    description: str
    skill_tags: List[str] = Field(default_factory=list)
    difficulty: Optional[str] = Field(None, description="easy, medium, hard")


class CurriculumTopic(BaseModel):
    """A curriculum topic with objectives"""
    topic_id: str = Field(..., description="Unique ID (e.g., 't1_greetings')")
    name: str
    description: Optional[str] = None
    order: int = Field(..., description="Sequential order in curriculum")
    objectives: List[LearningObjective]
    estimated_hours: Optional[float] = None


# ============================================
# OER Source Schemas
# ============================================

class SourceType(str, Enum):
    """Type of OER source"""
    OFFICIAL_CURRICULUM = "OFFICIAL_CURRICULUM"
    UNIVERSITY_OER = "UNIVERSITY_OER"
    EDUCATIONAL_PLATFORM = "EDUCATIONAL_PLATFORM"  # Khan Academy, etc.
    GOVERNMENT_RESOURCE = "GOVERNMENT_RESOURCE"
    NGO_CONTENT = "NGO_CONTENT"
    COMMUNITY_CONTENT = "COMMUNITY_CONTENT"


class LicenseType(str, Enum):
    """Open license types"""
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


class ScoringBreakdown(BaseModel):
    """Detailed scoring for a source"""
    authority: int = Field(..., ge=0, le=5, description="0-5: Source authority")
    alignment: int = Field(..., ge=0, le=5, description="0-5: Curriculum alignment")
    license: int = Field(..., ge=0, le=5, description="0-5: License openness")
    extractability: int = Field(..., ge=0, le=3, description="0-3: Content extraction ease")
    total: int = Field(..., ge=0, description="Sum of all scores")
    notes: Optional[str] = None


class DiscoveredSource(BaseModel):
    """An OER source discovered by the agent"""
    url: HttpUrl
    title: str
    publisher: str
    source_type: SourceType
    license: LicenseType
    license_url: Optional[HttpUrl] = None
    scoring: ScoringBreakdown
    topics_covered: List[str] = Field(default_factory=list)  # topic_ids
    objectives_addressed: List[str] = Field(default_factory=list)  # objective_ids
    content_format: Optional[str] = Field(None, description="PDF, HTML, VIDEO, etc.")
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# Output Schemas
# ============================================

class CurriculumMap(BaseModel):
    """Complete curriculum map with vetted sources"""
    curriculum_id: str = Field(..., description="Unique curriculum ID")
    metadata: CurriculumDiscoveryRequest
    official_documents: List[OfficialDocument]
    topics: List[CurriculumTopic]
    vetted_sources: List[DiscoveredSource]
    statistics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CurriculumDiscoveryResult(BaseModel):
    """Result of curriculum discovery job"""
    success: bool
    curriculum_map: Optional[CurriculumMap] = None
    error_message: Optional[str] = None
    sources_discovered: int = 0
    sources_vetted: int = 0
    duration_seconds: float = 0

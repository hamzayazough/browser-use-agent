"""
MongoDB document models using Motor
"""
from .base import PyObjectId
from .knowledge_chunk import (
    KnowledgeChunkModel,
    ChunkScope,
    ChunkType,
    SourceAttribution,
)
from .material import (
    MaterialModel,
    MaterialType,
    MaterialStatus,
)
from .job import (
    JobModel,
    JobStatus,
    JobType,
    JobPriority,
    JobInputData,
    JobOutputData,
    JobProgress,
    JobTiming,
    JobRetry,
    JobMetrics,
)
from .source_record import (
    SourceRecordModel,
    SourceType,
    LicenseType,
    VerificationStatus,
    ScoringBreakdown,
    ContentMetadata,
    VerificationInfo,
    ExtractionMetrics,
)
from .content_pack import (
    ContentPackModel,
    PackType,
    PackStatus,
    ApprovalStatus,
    AuthorityLevel,
    Jurisdiction,
    PackMetadata,
    OfficialSourceDocument,
    CurriculumInfo,
    MaterialSource,
    PackStatistics,
    QualityAssurance,
    Deployment,
    UsageGuidelines,
    SessionPlan,
    RoadmapTemplateInfo,
)

__all__ = [
    # Base
    "PyObjectId",
    # Knowledge Chunk
    "KnowledgeChunkModel",
    "ChunkScope",
    "ChunkType",
    "SourceAttribution",
    # Material
    "MaterialModel",
    "MaterialType",
    "MaterialStatus",
    # Job
    "JobModel",
    "JobStatus",
    "JobType",
    "JobPriority",
    "JobInputData",
    "JobOutputData",
    "JobProgress",
    "JobTiming",
    "JobRetry",
    "JobMetrics",
    # Source Record
    "SourceRecordModel",
    "SourceType",
    "LicenseType",
    "VerificationStatus",
    "ScoringBreakdown",
    "ContentMetadata",
    "VerificationInfo",
    "ExtractionMetrics",
    # Content Pack
    "ContentPackModel",
    "PackType",
    "PackStatus",
    "ApprovalStatus",
    "AuthorityLevel",
    "Jurisdiction",
    "PackMetadata",
    "OfficialSourceDocument",
    "CurriculumInfo",
    "MaterialSource",
    "PackStatistics",
    "QualityAssurance",
    "Deployment",
    "UsageGuidelines",
    "SessionPlan",
    "RoadmapTemplateInfo",
]

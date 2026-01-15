"""
Job tracking MongoDB models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from .base import PyObjectId


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"


class JobType(str, Enum):
    CURRICULUM_DISCOVERY = "CURRICULUM_DISCOVERY"
    CONTENT_EXTRACTION = "CONTENT_EXTRACTION"
    VALIDATION_COVERAGE = "VALIDATION_COVERAGE"
    PUBLISH_PACK = "PUBLISH_PACK"
    EMBEDDING_GENERATION = "EMBEDDING_GENERATION"
    SOURCE_VERIFICATION = "SOURCE_VERIFICATION"


class JobPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class JobInputData(BaseModel):
    country: Optional[str] = None
    region: Optional[str] = None
    grade: Optional[str] = None
    subject: Optional[str] = None
    language: Optional[str] = None
    curriculum_id: Optional[str] = None
    pack_id: Optional[str] = None
    source_ids: List[str] = Field(default_factory=list)
    chunk_ids: List[str] = Field(default_factory=list)
    additional_params: Optional[Dict[str, Any]] = None


class JobOutputData(BaseModel):
    curriculum_id: Optional[str] = None
    pack_id: Optional[str] = None
    source_ids: List[str] = Field(default_factory=list)
    chunk_ids: List[str] = Field(default_factory=list)
    sources_discovered: Optional[int] = None
    chunks_created: Optional[int] = None
    validation_passed: Optional[bool] = None
    coverage_score: Optional[float] = None
    published_at: Optional[datetime] = None
    additional_results: Optional[Dict[str, Any]] = None


class JobProgress(BaseModel):
    percentage: int = Field(default=0, ge=0, le=100)
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    completed_steps: Optional[int] = None
    message: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class JobTiming(BaseModel):
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    estimated_remaining_ms: Optional[int] = None


class JobRetry(BaseModel):
    attempt_number: int = 0
    max_attempts: int = 3
    previous_errors: List[str] = Field(default_factory=list)
    next_retry_at: Optional[datetime] = None


class JobMetrics(BaseModel):
    browser_actions_count: Optional[int] = None
    pages_visited: Optional[int] = None
    api_calls_count: Optional[int] = None
    tokens_used: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    memory_used_mb: Optional[float] = None


class JobModel(BaseModel):
    """MongoDB document model for background jobs"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    job_id: str
    job_type: JobType
    status: JobStatus = JobStatus.QUEUED
    priority: JobPriority = JobPriority.NORMAL
    input_data: JobInputData
    output_data: Optional[JobOutputData] = None
    progress: JobProgress = Field(default_factory=JobProgress)
    timing: JobTiming = Field(default_factory=JobTiming)
    retry: Optional[JobRetry] = None
    metrics: Optional[JobMetrics] = None
    error_message: Optional[str] = None
    error_stack: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    parent_job_id: Optional[str] = None
    child_job_ids: List[str] = Field(default_factory=list)
    triggered_by: Optional[str] = None
    worker_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    result_url: Optional[str] = None
    notification_sent: bool = False
    notification_recipient: Optional[str] = None
    deleted: bool = False

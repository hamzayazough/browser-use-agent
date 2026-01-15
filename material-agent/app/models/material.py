"""
Material MongoDB models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

from .base import PyObjectId


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
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    material_id: str
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

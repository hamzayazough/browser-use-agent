"""
MongoDB model for cached known OER sources
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime


class KnownSource(BaseModel):
    """
    Pre-vetted OER sources cached by country/region
    
    These are trusted sources that don't need re-vetting, saving time and cost
    """
    source_key: str = Field(..., description="Unique key: {country}_{region}_{subject}_{source_name}")
    
    # Location metadata
    country: str = Field(..., description="2-letter country code (e.g., 'US', 'CA')")
    region: Optional[str] = Field(None, description="State/province code (e.g., 'CA', 'QC')")
    
    # Source metadata
    source_name: str = Field(..., description="Source name (e.g., 'Khan Academy', 'CA Dept of Education')")
    base_url: HttpUrl = Field(..., description="Base URL for the source")
    publisher: str = Field(..., description="Publisher/organization name")
    
    # Applicability
    subjects: List[str] = Field(default_factory=list, description="Subjects covered (e.g., ['Mathematics', 'Science'])")
    grade_range: str = Field(..., description="Grade range (e.g., 'K-12', '4-8', '9-12')")
    language: str = Field(default="en", description="Language code")
    
    # Search patterns
    url_pattern: str = Field(..., description="URL pattern for finding content (e.g., '/math/grade-{grade}/')")
    search_query_template: Optional[str] = Field(
        None,
        description="Template for search queries (e.g., 'site:khanacademy.org {subject} grade {grade}')"
    )
    
    # Quality metadata
    license_type: str = Field(default="CC-BY-NC-SA", description="Default license type")
    authority_score: int = Field(..., ge=1, le=5, description="Pre-assigned authority score (1-5)")
    content_format: str = Field(default="HTML", description="Primary content format (HTML, PDF, VIDEO)")
    
    # Caching metadata
    is_active: bool = Field(default=True, description="Whether this source is currently active")
    last_verified: datetime = Field(default_factory=datetime.utcnow, description="Last verification date")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional metadata
    notes: Optional[str] = Field(None, description="Additional notes or instructions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_key": "us_ca_mathematics_khan_academy",
                "country": "US",
                "region": "CA",
                "source_name": "Khan Academy",
                "base_url": "https://www.khanacademy.org",
                "publisher": "Khan Academy",
                "subjects": ["Mathematics", "Science"],
                "grade_range": "K-12",
                "language": "en",
                "url_pattern": "/math/cc-{grade}-math",
                "search_query_template": "site:khanacademy.org {subject} grade {grade}",
                "license_type": "CC-BY-NC-SA",
                "authority_score": 4,
                "content_format": "HTML",
                "is_active": True
            }
        }

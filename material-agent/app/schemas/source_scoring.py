"""
Scoring rubric and utilities for OER sources
"""
from pydantic import BaseModel, Field
from typing import Dict


class ScoringRubric(BaseModel):
    """Rubric for scoring OER sources"""
    
    # Authority Scoring (0-5)
    authority_scores: Dict[str, int] = {
        "OFFICIAL_CURRICULUM": 5,      # Official curriculum documents
        "OFFICIAL_GOVERNMENT": 5,      # Ministry of Education
        "UNIVERSITY_OER": 4,           # University OER
        "UNIVERSITY": 4,                # University-published
        "EDUCATIONAL_NGO": 3,          # Non-profit education org
        "EDUCATIONAL_PLATFORM": 3,     # Khan Academy, Coursera
        "GOVERNMENT_RESOURCE": 4,      # Government websites
        "NGO_CONTENT": 3,              # NGO content
        "COMMUNITY_CONTENT": 2,        # Community-created
        "COMMUNITY": 2,                # Community-created
    }
    
    # License Scoring (0-5)
    license_scores: Dict[str, int] = {
        "CC-BY": 5,           # Most open
        "CC-BY-SA": 5,
        "CC0": 5,
        "PUBLIC-DOMAIN": 5,
        "CC-BY-NC": 4,
        "CC-BY-NC-SA": 4,
        "CUSTOM_OER": 3,
        "CC-BY-ND": 2,
        "CC-BY-NC-ND": 2,
        "PROPRIETARY": 0,     # Not acceptable
    }
    
    # Extractability Scoring (0-3)
    extractability_notes: Dict[str, int] = {
        "HTML": 3,           # Easy to extract
        "TEXT": 3,
        "PDF": 2,            # Moderate extraction
        "VIDEO": 1,          # Needs transcription
        "INTERACTIVE": 1,    # Complex extraction
        "PROPRIETARY": 0,    # Cannot extract
    }


class ScoringWeights(BaseModel):
    """Weights for scoring components"""
    authority_weight: float = Field(default=1.0, ge=0, le=1.0)
    alignment_weight: float = Field(default=1.0, ge=0, le=1.0)
    license_weight: float = Field(default=1.0, ge=0, le=1.0)
    extractability_weight: float = Field(default=1.0, ge=0, le=1.0)
    
    # Thresholds
    minimum_total_score: int = Field(default=12, description="Minimum to pass vetting")
    minimum_license_score: int = Field(default=3, description="Minimum for open license")

"""
OER Source Scoring Service
Scores sources based on authority, alignment, license, and extractability
"""
from typing import List
import logging

from app.schemas.curriculum_discovery import (
    DiscoveredSource,
    ScoringBreakdown,
    SourceType,
    LicenseType,
    CurriculumTopic,
)
from app.schemas.source_scoring import ScoringRubric

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for scoring OER sources"""
    
    def __init__(self):
        self.rubric = ScoringRubric()
    
    def score_source(
        self,
        source: DiscoveredSource,
        topics: List[CurriculumTopic],
        manual_alignment_score: int = None
    ) -> ScoringBreakdown:
        """
        Score an OER source
        
        Args:
            source: The discovered source
            topics: List of curriculum topics
            manual_alignment_score: Optional manual alignment score (0-5)
            
        Returns:
            ScoringBreakdown with detailed scores
        """
        # 1. Authority Score (0-5)
        authority_score = self._score_authority(source.source_type)
        
        # 2. Alignment Score (0-5)
        if manual_alignment_score is not None:
            alignment_score = manual_alignment_score
        else:
            alignment_score = self._score_alignment(source, topics)
        
        # 3. License Score (0-5)
        license_score = self._score_license(source.license)
        
        # 4. Extractability Score (0-3)
        extractability_score = self._score_extractability(source.content_format)
        
        # 5. Calculate Total
        total_score = (
            authority_score +
            alignment_score +
            license_score +
            extractability_score
        )
        
        # 6. Generate Notes
        notes = self._generate_scoring_notes(
            authority_score,
            alignment_score,
            license_score,
            extractability_score,
            source
        )
        
        return ScoringBreakdown(
            authority=authority_score,
            alignment=alignment_score,
            license=license_score,
            extractability=extractability_score,
            total=total_score,
            notes=notes
        )
    
    def _score_authority(self, source_type: SourceType) -> int:
        """Score based on source authority (0-5)"""
        return self.rubric.authority_scores.get(source_type.value, 2)
    
    def _score_license(self, license_type: LicenseType) -> int:
        """Score based on license openness (0-5)"""
        return self.rubric.license_scores.get(license_type.value, 0)
    
    def _score_extractability(self, content_format: str) -> int:
        """Score based on content extractability (0-3)"""
        if not content_format:
            return 2  # Assume moderate extractability
        
        content_format = content_format.upper()
        return self.rubric.extractability_notes.get(content_format, 2)
    
    def _score_alignment(
        self,
        source: DiscoveredSource,
        topics: List[CurriculumTopic]
    ) -> int:
        """
        Score curriculum alignment (0-5)
        
        Logic:
        - 5: Covers multiple objectives across multiple topics
        - 4: Covers multiple objectives in one topic
        - 3: Covers 1-2 objectives
        - 2: Related but not directly aligned
        - 1: Tangentially related
        - 0: Not aligned
        """
        objectives_covered = len(source.objectives_addressed)
        topics_covered = len(source.topics_covered)
        
        if objectives_covered >= 5 and topics_covered >= 2:
            return 5
        elif objectives_covered >= 3 and topics_covered >= 1:
            return 4
        elif objectives_covered >= 2:
            return 3
        elif objectives_covered == 1:
            return 3
        elif topics_covered >= 1:
            return 2
        else:
            return 1
    
    def _generate_scoring_notes(
        self,
        authority: int,
        alignment: int,
        license: int,
        extractability: int,
        source: DiscoveredSource
    ) -> str:
        """Generate human-readable scoring notes"""
        notes = []
        
        if authority >= 4:
            notes.append("High authority source")
        elif authority <= 2:
            notes.append("Lower authority - community content")
        
        if alignment >= 4:
            notes.append("Excellent curriculum alignment")
        elif alignment <= 2:
            notes.append("Limited alignment to objectives")
        
        if license >= 4:
            notes.append("Open license - allows derivatives")
        elif license <= 2:
            notes.append("Restrictive license")
        
        if extractability >= 2:
            notes.append("Easy content extraction")
        elif extractability == 1:
            notes.append("Moderate extraction difficulty")
        
        return "; ".join(notes)
    
    def filter_vetted_sources(
        self,
        sources: List[DiscoveredSource],
        minimum_total_score: int = 12,
        minimum_license_score: int = 3
    ) -> List[DiscoveredSource]:
        """
        Filter sources that meet minimum criteria
        
        Args:
            sources: List of discovered sources
            minimum_total_score: Minimum total score (default: 12)
            minimum_license_score: Minimum license score (default: 3)
            
        Returns:
            List of vetted sources
        """
        vetted = []
        
        for source in sources:
            if (
                source.scoring.total >= minimum_total_score and
                source.scoring.license >= minimum_license_score
            ):
                vetted.append(source)
                logger.info(f"✅ Vetted: {source.title} (score: {source.scoring.total})")
            else:
                logger.info(f"❌ Rejected: {source.title} (score: {source.scoring.total})")
        
        return vetted

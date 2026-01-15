"""
Unit tests for Curriculum Discovery Service
"""
import pytest
import asyncio
from app.schemas.curriculum_discovery import (
    CurriculumDiscoveryRequest,
    DiscoveredSource,
    SourceType,
    LicenseType,
    ScoringBreakdown,
)
from app.services.scoring_service import ScoringService


@pytest.fixture
def scoring_service():
    return ScoringService()


@pytest.fixture
def sample_source():
    return DiscoveredSource(
        url="https://khanacademy.org/spanish/greetings",
        title="Spanish Greetings",
        publisher="Khan Academy",
        source_type=SourceType.EDUCATIONAL_PLATFORM,
        license=LicenseType.CC_BY_NC_SA,
        content_format="HTML",
        scoring=ScoringBreakdown(
            authority=3,
            alignment=4,
            license=4,
            extractability=3,
            total=14
        )
    )


def test_scoring_service_authority(scoring_service):
    """Test authority scoring"""
    score = scoring_service._score_authority(SourceType.OFFICIAL_CURRICULUM)
    assert score == 5
    
    score = scoring_service._score_authority(SourceType.COMMUNITY_CONTENT)
    assert score == 2


def test_scoring_service_license(scoring_service):
    """Test license scoring"""
    score = scoring_service._score_license(LicenseType.CC_BY)
    assert score == 5
    
    score = scoring_service._score_license(LicenseType.PROPRIETARY)
    assert score == 0


def test_filter_vetted_sources(scoring_service, sample_source):
    """Test source filtering"""
    sources = [sample_source]
    vetted = scoring_service.filter_vetted_sources(
        sources,
        minimum_total_score=12,
        minimum_license_score=3
    )
    assert len(vetted) == 1


@pytest.mark.asyncio
async def test_curriculum_discovery_request_validation():
    """Test request validation"""
    request = CurriculumDiscoveryRequest(
        country="CA",
        region="QC",
        grade="4",
        subject="Spanish",
        language="fr-CA"
    )
    assert request.country == "CA"
    assert request.grade == "4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

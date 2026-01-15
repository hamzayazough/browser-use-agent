"""
Service for managing and querying cached known OER sources
"""
import logging
from typing import List, Optional

from app.models.known_source import KnownSource
from app.repositories.known_source_repository import KnownSourceRepository
from app.schemas.curriculum_discovery import CurriculumDiscoveryRequest, DiscoveredSource, SourceType, LicenseType
from pydantic import HttpUrl

logger = logging.getLogger(__name__)


class KnownSourceService:
    """Service for known OER sources"""
    
    def __init__(self, db_connection):
        """
        Initialize service
        
        Args:
            db_connection: MongoDB database connection
        """
        self.repo = KnownSourceRepository(db_connection)
    
    async def get_cached_sources(
        self,
        request: CurriculumDiscoveryRequest
    ) -> List[DiscoveredSource]:
        """
        Get cached known sources for a curriculum request
        
        Args:
            request: Curriculum discovery request
            
        Returns:
            List of DiscoveredSource objects from cached sources
        """
        # Find matching known sources
        known_sources = await self.repo.find_by_location(
            country=request.country,
            region=request.region,
            subject=request.subject,
            grade=request.grade
        )
        
        if not known_sources:
            logger.info(f"No cached sources found for {request.country}/{request.region}/{request.subject}")
            return []
        
        logger.info(f"Found {len(known_sources)} cached known sources")
        
        # Convert to DiscoveredSource objects
        discovered_sources = []
        
        for known in known_sources:
            # Build specific URL from pattern
            url = self._build_url(known, request)
            
            discovered = DiscoveredSource(
                url=HttpUrl(url),
                title=f"{known.source_name} - {request.subject} Grade {request.grade}",
                publisher=known.publisher,
                source_type=self._map_source_type(known.source_name),
                license=self._map_license_type(known.license_type),
                license_url=HttpUrl(f"{known.base_url}/license") if known.base_url else None,
                content_format=known.content_format,
                description=f"Cached known source: {known.source_name}",
                topics_covered=[],  # Will be filled later
                objectives_addressed=[],  # Will be filled later
                is_from_cache=True  # Custom flag to indicate it's cached
            )
            
            discovered_sources.append(discovered)
        
        return discovered_sources
    
    def _build_url(self, known: KnownSource, request: CurriculumDiscoveryRequest) -> str:
        """
        Build specific URL from known source pattern
        
        Args:
            known: Known source with URL pattern
            request: Discovery request with grade/subject
            
        Returns:
            Formatted URL
        """
        base = str(known.base_url)
        
        if known.url_pattern:
            # Replace placeholders in pattern
            pattern = known.url_pattern.replace("{grade}", request.grade)
            pattern = pattern.replace("{subject}", request.subject.lower())
            return f"{base}{pattern}"
        
        return base
    
    def _map_source_type(self, source_name: str) -> SourceType:
        """Map source name to SourceType enum"""
        source_name_lower = source_name.lower()
        
        if "khan" in source_name_lower:
            return SourceType.EDUCATIONAL_PLATFORM
        elif "gov" in source_name_lower or "department" in source_name_lower:
            return SourceType.GOVERNMENT_RESOURCE
        elif "university" in source_name_lower or "edu" in source_name_lower:
            return SourceType.UNIVERSITY_OER
        else:
            return SourceType.EDUCATIONAL_PLATFORM
    
    def _map_license_type(self, license_str: str) -> LicenseType:
        """Map license string to LicenseType enum"""
        try:
            return LicenseType(license_str)
        except ValueError:
            return LicenseType.CUSTOM_OER
    
    async def initialize_default_sources(self):
        """
        Initialize database with default known sources
        
        Call this once to populate the database with common sources
        """
        default_sources = [
            # Khan Academy - US
            KnownSource(
                source_key="us_all_mathematics_khan_academy",
                country="US",
                region=None,  # Works for all US states
                source_name="Khan Academy",
                base_url=HttpUrl("https://www.khanacademy.org"),
                publisher="Khan Academy",
                subjects=["Mathematics", "Science", "Computing"],
                grade_range="K-12",
                language="en",
                url_pattern="/math/cc-{grade}-math",
                search_query_template="site:khanacademy.org {subject} grade {grade}",
                license_type="CC-BY-NC-SA",
                authority_score=4,
                content_format="HTML"
            ),
            
            # Khan Academy - CA specific
            KnownSource(
                source_key="us_ca_mathematics_khan_academy",
                country="US",
                region="CA",
                source_name="Khan Academy - California Standards",
                base_url=HttpUrl("https://www.khanacademy.org"),
                publisher="Khan Academy",
                subjects=["Mathematics"],
                grade_range="K-12",
                language="en",
                url_pattern="/math/cc-{grade}-math",
                search_query_template="site:khanacademy.org California standards {subject} grade {grade}",
                license_type="CC-BY-NC-SA",
                authority_score=4,
                content_format="HTML"
            ),
            
            # California Department of Education
            KnownSource(
                source_key="us_ca_all_ca_dept_education",
                country="US",
                region="CA",
                source_name="California Department of Education",
                base_url=HttpUrl("https://www.cde.ca.gov"),
                publisher="California Department of Education",
                subjects=["Mathematics", "Science", "English Language Arts", "History"],
                grade_range="K-12",
                language="en",
                url_pattern="/ci/",
                search_query_template="site:cde.ca.gov {subject} grade {grade} curriculum",
                license_type="PUBLIC-DOMAIN",
                authority_score=5,
                content_format="PDF"
            ),
            
            # OpenStax - College level
            KnownSource(
                source_key="us_all_mathematics_openstax",
                country="US",
                region=None,
                source_name="OpenStax",
                base_url=HttpUrl("https://openstax.org"),
                publisher="OpenStax",
                subjects=["Mathematics", "Science", "Social Sciences"],
                grade_range="9-12",
                language="en",
                url_pattern="/subjects",
                search_query_template="site:openstax.org {subject}",
                license_type="CC-BY",
                authority_score=5,
                content_format="PDF"
            ),
            
            # CK-12 Foundation
            KnownSource(
                source_key="us_all_all_ck12",
                country="US",
                region=None,
                source_name="CK-12 Foundation",
                base_url=HttpUrl("https://www.ck12.org"),
                publisher="CK-12 Foundation",
                subjects=["Mathematics", "Science", "History", "English"],
                grade_range="K-12",
                language="en",
                url_pattern="/student/",
                search_query_template="site:ck12.org {subject} grade {grade}",
                license_type="CC-BY-NC",
                authority_score=4,
                content_format="HTML"
            ),
            
            # TODO: Add more sources for other countries/regions
            # - Canada (various provinces)
            # - UK
            # - Australia
            # etc.
        ]
        
        # Bulk create
        await self.repo.bulk_create(default_sources)
        logger.info(f"Initialized {len(default_sources)} default known sources")

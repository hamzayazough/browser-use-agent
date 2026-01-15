"""
Curriculum Discovery Service (Job 1)
Main orchestrator for discovering curricula and curating OER sources
"""
import asyncio
import logging
from typing import List, Optional
from datetime import datetime
import uuid

from app.schemas.curriculum_discovery import (
    CurriculumDiscoveryRequest,
    CurriculumDiscoveryResult,
    CurriculumMap,
    CurriculumTopic,
    OfficialDocument,
    DiscoveredSource,
    AuthorityLevel,
    SourceType,
    LicenseType,
)
from app.services.scoring_service import ScoringService
from app.utils.browser_use_helpers import BrowserUseHelper
from app.repositories.source_record_repository import SourceRecordRepository
from app.models.source_record import SourceRecordModel

logger = logging.getLogger(__name__)


class CurriculumDiscoveryService:
    """
    Service for discovering curricula and curating OER sources
    
    This is Job 1 in the 4-stage content pack pipeline:
    1. CURRICULUM_DISCOVERY (this service)
    2. CONTENT_EXTRACTION
    3. VALIDATION_COVERAGE
    4. PUBLISH_PACK
    """
    
    def __init__(
        self,
        db_connection: any,
        browser_use_api_key: Optional[str] = None,
        use_cloud: bool = True
    ):
        """
        Initialize Curriculum Discovery Service
        
        Args:
            db_connection: MongoDB database connection
            browser_use_api_key: API key for Browser-Use
            use_cloud: Use Browser-Use cloud browser (recommended)
        """
        self.browser_helper = BrowserUseHelper(
            use_cloud=use_cloud,
            browser_use_api_key=browser_use_api_key
        )
        self.scoring_service = ScoringService()
        self.source_repo = SourceRecordRepository(db_connection)
    
    async def discover_curriculum(
        self,
        request: CurriculumDiscoveryRequest
    ) -> CurriculumDiscoveryResult:
        """
        Main entry point for curriculum discovery
        
        Args:
            request: Discovery request parameters
            
        Returns:
            CurriculumDiscoveryResult with curriculum map or error
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting curriculum discovery: {request.subject} - {request.grade}")
            
            # Step 1: Discover official curriculum documents
            logger.info("Step 1: Discovering official documents...")
            official_docs = await self._discover_curriculum_documents(request)
            
            if not official_docs:
                return CurriculumDiscoveryResult(
                    success=False,
                    error_message="No official curriculum documents found"
                )
            
            # Step 2: Extract topics and objectives from documents
            logger.info("Step 2: Extracting topics and objectives...")
            topics = await self._extract_topics_objectives(official_docs, request)
            
            if not topics:
                return CurriculumDiscoveryResult(
                    success=False,
                    error_message="Failed to extract curriculum structure"
                )
            
            # Step 3: Search for OER sources
            logger.info("Step 3: Searching for OER sources...")
            discovered_sources = await self._search_oer_sources(topics, request)
            
            # Step 4: Score and filter sources
            logger.info("Step 4: Scoring and filtering sources...")
            vetted_sources = self.scoring_service.filter_vetted_sources(
                discovered_sources,
                minimum_total_score=12,
                minimum_license_score=3
            )
            
            # Step 5: Save vetted sources to MongoDB
            logger.info("Step 5: Saving source records to database...")
            curriculum_id = self._generate_curriculum_id(request)
            await self._save_source_records(curriculum_id, vetted_sources, topics)
            
            # Step 6: Build curriculum map
            curriculum_map = CurriculumMap(
                curriculum_id=curriculum_id,
                metadata=request,
                official_documents=official_docs,
                topics=topics,
                vetted_sources=vetted_sources,
                statistics={
                    "total_topics": len(topics),
                    "total_objectives": sum(len(t.objectives) for t in topics),
                    "sources_discovered": len(discovered_sources),
                    "sources_vetted": len(vetted_sources),
                    "average_source_score": sum(s.scoring.total for s in vetted_sources) / len(vetted_sources) if vetted_sources else 0
                }
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Discovery complete: {len(vetted_sources)} vetted sources in {duration:.2f}s")
            
            return CurriculumDiscoveryResult(
                success=True,
                curriculum_map=curriculum_map,
                sources_discovered=len(discovered_sources),
                sources_vetted=len(vetted_sources),
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Curriculum discovery failed: {str(e)}", exc_info=True)
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return CurriculumDiscoveryResult(
                success=False,
                error_message=str(e),
                duration_seconds=duration
            )
    
    async def _discover_curriculum_documents(
        self,
        request: CurriculumDiscoveryRequest
    ) -> List[OfficialDocument]:
        """
        Step 1: Discover official curriculum documents
        
        Uses Browser-Use agent to search for official curriculum docs
        
        Args:
            request: Discovery request
            
        Returns:
            List of official documents
        """
        # Build search query
        search_terms = [
            f"{request.country} {request.region or ''} official curriculum",
            request.subject,
            f"grade {request.grade}",
            request.language
        ]
        search_query = " ".join(filter(None, search_terms))
        
        # Create agent task
        task = f"""
        Search for official curriculum documents:
        
        Query: {search_query}
        
        Instructions:
        1. Search Google for official government curriculum documents
        2. Look for domains like .gov, .edu, official ministry websites
        3. Find documents from:
           - Ministry/Department of Education
           - Official government education websites
           - State/provincial education authorities
        4. For each document found, extract:
           - Title
           - URL
           - Publisher
           - Publication date (if available)
           - PDF link (if available)
        5. Return top 5 most authoritative documents
        6. Use 'done' action when complete
        """
        
        # Run agent with structured output
        from pydantic import BaseModel
        
        class DocumentsOutput(BaseModel):
            documents: List[OfficialDocument]
        
        result = await self.browser_helper.extract_structured_data(
            task=task,
            output_model=DocumentsOutput,
            max_steps=50
        )
        
        if result and result.documents:
            # Set authority level to OFFICIAL_GOVERNMENT
            for doc in result.documents:
                doc.authority_level = AuthorityLevel.OFFICIAL_GOVERNMENT
            return result.documents
        
        return []
    
    async def _extract_topics_objectives(
        self,
        official_docs: List[OfficialDocument],
        request: CurriculumDiscoveryRequest
    ) -> List[CurriculumTopic]:
        """
        Step 2: Extract topics and learning objectives from official documents
        
        Uses Browser-Use agent to parse curriculum structure
        
        Args:
            official_docs: Official curriculum documents
            request: Discovery request
            
        Returns:
            List of curriculum topics with objectives
        """
        # Use the first (most authoritative) document
        primary_doc = official_docs[0]
        
        # Create parsing task
        task = f"""
        Parse curriculum structure from official document:
        
        Document URL: {primary_doc.url}
        Subject: {request.subject}
        Grade: {request.grade}
        
        Instructions:
        1. Navigate to the document
        2. Extract the curriculum structure:
           - Main topics (units, modules, themes)
           - Learning objectives for each topic
           - Sequential order
        3. For each topic, extract:
           - Topic name
           - Description
           - Learning objectives (what students should learn)
           - Estimated hours (if available)
        4. Generate unique IDs:
           - Topics: t1_topic_name, t2_topic_name, etc.
           - Objectives: obj_topic_001, obj_topic_002, etc.
        5. Return structured data with clear hierarchy
        6. Use 'done' action when complete
        """
        
        # Run agent with structured output
        from pydantic import BaseModel
        
        class TopicsOutput(BaseModel):
            topics: List[CurriculumTopic]
        
        result = await self.browser_helper.extract_structured_data(
            task=task,
            output_model=TopicsOutput,
            max_steps=100
        )
        
        if result and result.topics:
            return result.topics
        
        return []
    
    async def _search_oer_sources(
        self,
        topics: List[CurriculumTopic],
        request: CurriculumDiscoveryRequest
    ) -> List[DiscoveredSource]:
        """
        Step 3: Search for Open Educational Resources
        
        Uses Browser-Use agent to search for OER materials
        
        Args:
            topics: Curriculum topics
            request: Discovery request
            
        Returns:
            List of discovered sources
        """
        all_sources = []
        
        # Search for sources topic by topic
        for topic in topics[:5]:  # Limit to first 5 topics for MVP
            logger.info(f"Searching OER for topic: {topic.name}")
            
            # Build search query
            search_query = f"{topic.name} {request.subject} grade {request.grade} OER open educational resources"
            
            # Create search task
            task = f"""
            Search for Open Educational Resources (OER):
            
            Topic: {topic.name}
            Subject: {request.subject}
            Grade: {request.grade}
            
            Instructions:
            1. Search for OER materials from trusted sources:
               - Khan Academy (khanacademy.org)
               - OpenStax (openstax.org)
               - OER Commons (oercommons.org)
               - MIT OpenCourseWare (ocw.mit.edu)
               - CK-12 Foundation (ck12.org)
               - Government education websites
            
            2. For each resource found, extract:
               - Title
               - URL
               - Publisher
               - License type (CC-BY, CC-BY-SA, etc.)
               - Content format (PDF, HTML, VIDEO, etc.)
               - Description
            
            3. Find 3-5 resources per topic
            4. Verify license is open (Creative Commons, Public Domain)
            5. Return structured data
            6. Use 'done' action when complete
            """
            
            # Run agent
            from pydantic import BaseModel
            
            class SourcesOutput(BaseModel):
                sources: List[DiscoveredSource]
            
            result = await self.browser_helper.extract_structured_data(
                task=task,
                output_model=SourcesOutput,
                max_steps=80
            )
            
            if result and result.sources:
                # Set topic and objectives for each source
                for source in result.sources:
                    source.topics_covered = [topic.topic_id]
                    source.objectives_addressed = [obj.objective_id for obj in topic.objectives[:3]]
                    
                    # Score the source
                    source.scoring = self.scoring_service.score_source(
                        source=source,
                        topics=topics
                    )
                
                all_sources.extend(result.sources)
            
            # Rate limiting (optional)
            await asyncio.sleep(2)
        
        return all_sources
    
    async def _save_source_records(
        self,
        curriculum_id: str,
        vetted_sources: List[DiscoveredSource],
        topics: List[CurriculumTopic]
    ):
        """
        Step 5: Save vetted sources to MongoDB
        
        Args:
            curriculum_id: Unique curriculum ID
            vetted_sources: List of vetted sources
            topics: Curriculum topics (for topic/objective IDs)
        """
        for source in vetted_sources:
            # Generate source_id
            source_id = f"src_{uuid.uuid4().hex[:12]}"
            
            # Create SourceRecordModel
            source_record = SourceRecordModel(
                source_id=source_id,
                curriculum_id=curriculum_id,
                source_type=source.source_type,
                url=str(source.url),
                title=source.title,
                publisher=source.publisher,
                license=source.license,
                license_url=str(source.license_url) if source.license_url else "",
                scoring=source.scoring.model_dump(),
                topic_ids=source.topics_covered,
                objective_ids=source.objectives_addressed,
                discovered_at=source.discovered_at
            )
            
            # Save to database
            await self.source_repo.create(source_record)
            logger.info(f"Saved source record: {source_id}")
    
    def _generate_curriculum_id(self, request: CurriculumDiscoveryRequest) -> str:
        """Generate unique curriculum ID"""
        parts = [
            "cur",
            request.country.lower(),
            request.region.lower() if request.region else "",
            request.subject.lower().replace(" ", "_"),
            f"grade{request.grade}",
            "v1"
        ]
        return "_".join(filter(None, parts))

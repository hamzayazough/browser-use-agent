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
from app.services.known_source_service import KnownSourceService
from app.utils.browser_use_helpers import BrowserUseHelper
from app.utils.job_logger import JobLogger, JobType
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
        self.known_source_service = KnownSourceService(db_connection)
        self.source_repo = SourceRecordRepository(db_connection)
        self.job_logger = JobLogger()
    
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
        
        # Start job logging
        job_id = self.job_logger.start_job(
            JobType.CURRICULUM_DISCOVERY,
            {
                "country": request.country,
                "region": request.region,
                "subject": request.subject,
                "grade": request.grade,
                "language": request.language
            }
        )
        
        try:
            logger.info(f"Starting curriculum discovery: {request.subject} - {request.grade}")
            
            # Step 1: Discover official curriculum documents
            logger.info("Step 1: Discovering official documents...")
            official_docs = await self._discover_curriculum_documents(request)
            
            if not official_docs:
                self.job_logger.complete_job(
                    job_id,
                    success=False,
                    summary={},
                    error="No official curriculum documents found"
                )
                return CurriculumDiscoveryResult(
                    success=False,
                    error_message="No official curriculum documents found"
                )
            
            # Log discovered documents
            self.job_logger.log_discovery_documents(
                job_id,
                [
                    {
                        "title": doc.title,
                        "url": doc.url,
                        "publisher": doc.publisher,
                        "publication_date": doc.publication_date
                    }
                    for doc in official_docs
                ]
            )
            
            # Step 2: Extract topics and objectives from documents
            logger.info("Step 2: Extracting topics and objectives...")
            topics = await self._extract_topics_objectives(official_docs, request)
            
            if not topics:
                self.job_logger.complete_job(
                    job_id,
                    success=False,
                    summary={},
                    error="Failed to extract curriculum structure"
                )
                return CurriculumDiscoveryResult(
                    success=False,
                    error_message="Failed to extract curriculum structure"
                )
            
            # Log extracted topics
            self.job_logger.log_topics_extraction(
                job_id,
                [
                    {
                        "topic_id": topic.topic_id,
                        "name": topic.name,
                        "objectives": [obj.objective_id for obj in topic.objectives]
                    }
                    for topic in topics
                ]
            )
            
            # Step 3: Search for OER sources
            logger.info("Step 3: Searching for OER sources...")
            discovered_sources = await self._search_oer_sources(topics, request, job_id)
            
            # Step 4: Score and filter sources
            logger.info("Step 4: Scoring and filtering sources...")
            vetted_sources = self.scoring_service.filter_vetted_sources(
                discovered_sources,
                minimum_total_score=12,
                minimum_license_score=3
            )
            
            # Log vetting results
            self.job_logger.log_source_vetting(
                job_id,
                total_sources=len(discovered_sources),
                vetted_sources=len(vetted_sources),
                vetted_list=[
                    {
                        "title": src.title,
                        "score": src.scoring.total,
                        "source_type": src.source_type.value
                    }
                    for src in vetted_sources
                ]
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
            
            # Log job completion
            self.job_logger.complete_job(
                job_id,
                success=True,
                summary={
                    "curriculum_id": curriculum_id,
                    "total_topics": len(topics),
                    "total_objectives": sum(len(t.objectives) for t in topics),
                    "sources_discovered": len(discovered_sources),
                    "sources_vetted": len(vetted_sources),
                    "average_source_score": round(sum(s.scoring.total for s in vetted_sources) / len(vetted_sources), 2) if vetted_sources else 0
                }
            )
            
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
            
            # Log failure
            self.job_logger.complete_job(
                job_id,
                success=False,
                summary={},
                error=str(e)
            )
            
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
        
        Uses Browser-Use agent to parse curriculum structure with intelligent grouping
        
        Args:
            official_docs: Official curriculum documents
            request: Discovery request
            
        Returns:
            List of curriculum topics with objectives
        """
        # Use the first (most authoritative) document
        primary_doc = official_docs[0]
        
        # Create parsing task with intelligent grouping
        task = f"""
        Parse curriculum structure from official document:
        
        Document URL: {primary_doc.url}
        Subject: {request.subject}
        Grade: {request.grade}
        
        Instructions:
        1. Navigate to the document
        2. Identify ALL main curriculum topics/domains for Grade {request.grade}
        
        3. INTELLIGENT TOPIC GROUPING:
           - If there are 10+ topics: Review if some are too specific and can be grouped
           - Group topics ONLY if they are closely related and share similar concepts
           - DO NOT force grouping unrelated topics just to reduce the count
           - If all 10+ topics are distinct, keep them separate
           - Optimal: 5-9 well-defined topics, but quality > arbitrary count
           
           Example for Math Grade 4:
           - TOO SPECIFIC (should group): "Addition", "Subtraction", "Multiplication", "Division" → "Operations & Algebraic Thinking"
           - RELATED (should group): "Fractions - Addition", "Fractions - Subtraction" → "Operations with Fractions"
           - DISTINCT (keep separate): "Operations", "Geometry", "Measurement", "Data Analysis" → Keep all 4
           
           If topics are naturally distinct, keep them ALL even if 10+
           
        4. For EACH topic, extract:
           - Topic name (clear, descriptive)
           - Description (what the topic covers)
           - ALL learning objectives under that topic
           - Sequential order (1, 2, 3...)
           - Estimated hours (if mentioned, otherwise skip)
        
        5. For each learning objective:
           - Unique ID: obj_[topic_id]_[number]
           - Description: What students should be able to do
           - Keep objectives specific and actionable
        
        6. Generate unique IDs:
           - Topics: t1_operations, t2_fractions, etc. (use short keywords)
           - Objectives: obj_t1_001, obj_t1_002, etc.
        
        7. Return structured data with COMPLETE curriculum hierarchy
        8. Use 'done' action when all topics and objectives are extracted
        
        IMPORTANT: Extract ALL topics for the grade level, but group intelligently if there are too many.
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
        request: CurriculumDiscoveryRequest,
        job_id: str
    ) -> List[DiscoveredSource]:
        """
        Step 3: Search for Open Educational Resources
        
        OPTIMIZED: First checks cached known sources, then falls back to agent search
        
        Args:
            topics: Curriculum topics
            request: Discovery request
            job_id: Job ID for logging
            
        Returns:
            List of discovered sources
        """
        all_sources = []
        
        # OPTIMIZATION: Get cached known sources first
        logger.info("Checking cached known sources...")
        cached_sources = await self.known_source_service.get_cached_sources(request)
        
        if cached_sources:
            logger.info(f"✅ Found {len(cached_sources)} cached known sources - skipping agent search!")
            
            # Assign cached sources to topics (1 source per topic)
            for i, topic in enumerate(topics):
                if i < len(cached_sources):
                    source = cached_sources[i]
                    
                    # Set topic and objectives
                    source.topics_covered = [topic.topic_id]
                    source.objectives_addressed = [obj.objective_id for obj in topic.objectives]
                    
                    # Score the source
                    source.scoring = self.scoring_service.score_source(
                        source=source,
                        topics=topics
                    )
                    
                    all_sources.append(source)
                    
                    # Log cached source usage
                    self.job_logger.log_oer_search(
                        job_id,
                        topic_name=topic.name,
                        sources_found=1,
                        sources=[
                            {
                                "title": source.title,
                                "url": source.url,
                                "publisher": source.publisher,
                                "content_format": source.content_format,
                                "cached": True
                            }
                        ]
                    )
            
            return all_sources
        
        # FALLBACK: Use agent search if no cached sources (EXPENSIVE)
        logger.warning("No cached sources found - using agent search (this will be slow and costly)")
        
        # Search for sources for ALL topics (agent decides coverage)
        for topic in topics:
            logger.info(f"Searching OER for topic: {topic.name}")
            
            # Count objectives for this topic
            num_objectives = len(topic.objectives)
            
            # Create simplified search task (OPTIMIZED: only 1 source per topic)
            task = f"""
            Search for Open Educational Resources:
            
            Topic: {topic.name}
            Subject: {request.subject}
            Grade: {request.grade}
            Number of learning objectives: {num_objectives}
            
            Instructions:
            1. Search for OER materials from trusted sources:
               - Khan Academy (khanacademy.org) - priority #1
               - Government education sites (.gov, .edu) - priority #2
               - OpenStax, CK-12 if relevant
            
            2. Find ONLY 1 high-quality source that covers this topic
            
            3. For the source, extract:
               - Title
               - URL
               - Publisher
               - License type (if visible: CC-BY, CC-BY-SA, CC-BY-NC-SA, etc.)
               - Content format (PDF, HTML, VIDEO - avoid VIDEO)
               - Brief description
            
            4. Prioritize:
               - Khan Academy first (fast HTML content)
               - Government PDFs second
               - Avoid video sources (expensive to process)
            
            5. Use 'done' action when you found 1 good source
            """
            
            # Run agent with reduced max_steps (OPTIMIZED: 15 instead of 30)
            from pydantic import BaseModel
            
            class SourcesOutput(BaseModel):
                sources: List[DiscoveredSource]
            
            result = await self.browser_helper.extract_structured_data(
                task=task,
                output_model=SourcesOutput,
                max_steps=15  # OPTIMIZED: Reduced from 30
            )
            
            if result and result.sources:
                # Take only the first source (OPTIMIZED: limit 1)
                source = result.sources[0]
                
                # Set topic and objectives
                source.topics_covered = [topic.topic_id]
                source.objectives_addressed = [obj.objective_id for obj in topic.objectives]
                
                # Score the source
                source.scoring = self.scoring_service.score_source(
                    source=source,
                    topics=topics
                )
                
                all_sources.append(source)
                
                # Log OER search results for this topic
                self.job_logger.log_oer_search(
                    job_id,
                    topic_name=topic.name,
                    sources_found=1,
                    sources=[
                        {
                            "title": source.title,
                            "url": source.url,
                            "publisher": source.publisher,
                            "content_format": source.content_format
                        }
                    ]
                )
            
            # Small delay to avoid overwhelming the browser service
            await asyncio.sleep(1)
        
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

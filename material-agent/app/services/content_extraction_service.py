"""
Content Extraction Service (Job 2)
Extract content from OER sources and create knowledge chunks
"""
import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from app.schemas.content_extraction import (
    ContentExtractionRequest,
    ContentExtractionResult,
    SourceExtractionResult,
    SourceExtractionTask,
    KnowledgeChunkWithEmbedding,
    ChunkScope,
    ChunkingConfig,
    EmbeddingConfig
)
from app.services.embedding_service import EmbeddingService
from app.services.chunking_service import ChunkingService
from app.services.extractors import HTMLExtractor, PDFExtractor, VideoExtractor
from app.repositories.source_record_repository import SourceRecordRepository
from app.repositories.knowledge_chunk_repository import KnowledgeChunkRepository
from app.models.knowledge_chunk import KnowledgeChunkModel

logger = logging.getLogger(__name__)


class ContentExtractionService:
    """
    Service for extracting content and creating knowledge chunks
    
    This is Job 2 in the 4-stage content pack pipeline:
    1. CURRICULUM_DISCOVERY
    2. CONTENT_EXTRACTION (this service)
    3. VALIDATION_COVERAGE
    4. PUBLISH_PACK
    """
    
    def __init__(
        self,
        db_connection: any,
        openai_api_key: str,
        use_cloud: bool = True,
        chunking_config: Optional[ChunkingConfig] = None,
        embedding_config: Optional[EmbeddingConfig] = None
    ):
        """
        Initialize Content Extraction Service
        
        Args:
            db_connection: MongoDB database connection
            openai_api_key: OpenAI API key for embeddings
            use_cloud: Use Browser-Use cloud browser
            chunking_config: Optional chunking configuration
            embedding_config: Optional embedding configuration
        """
        # Repositories
        self.source_repo = SourceRecordRepository(db_connection)
        self.chunk_repo = KnowledgeChunkRepository(db_connection)
        
        # Services
        self.embedding_service = EmbeddingService(
            api_key=openai_api_key,
            config=embedding_config
        )
        self.chunking_service = ChunkingService(config=chunking_config)
        
        # Extractors
        self.extractors = [
            HTMLExtractor(use_cloud=use_cloud),
            PDFExtractor(),
            VideoExtractor()
        ]
    
    async def extract_content_from_sources(
        self,
        request: ContentExtractionRequest
    ) -> ContentExtractionResult:
        """
        Main entry point for content extraction
        
        Args:
            request: Extraction request parameters
            
        Returns:
            ContentExtractionResult with statistics
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting content extraction for curriculum: {request.curriculum_id}")
            
            # Step 1: Get vetted sources from database
            logger.info("Step 1: Retrieving vetted sources...")
            sources = await self._get_sources(request)
            
            if not sources:
                return ContentExtractionResult(
                    success=False,
                    curriculum_id=request.curriculum_id,
                    error_message="No sources found for extraction"
                )
            
            logger.info(f"Found {len(sources)} sources to process")
            
            # Step 2: Extract content from each source
            logger.info("Step 2: Extracting content from sources...")
            extraction_results = await self._extract_from_sources(sources)
            
            # Count successes
            successful_extractions = [r for r in extraction_results if r.success]
            total_chunks = sum(r.chunks_created for r in successful_extractions)
            
            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Log embedding statistics
            embedding_stats = self.embedding_service.get_usage_stats()
            logger.info(f"Embedding stats: {embedding_stats}")
            
            logger.info(
                f"✅ Extraction complete: {len(successful_extractions)}/{len(sources)} "
                f"sources processed, {total_chunks} chunks created in {duration:.2f}s"
            )
            
            return ContentExtractionResult(
                success=True,
                curriculum_id=request.curriculum_id,
                sources_processed=len(sources),
                sources_successful=len(successful_extractions),
                total_chunks_created=total_chunks,
                embeddings_generated=embedding_stats["total_api_calls"],
                duration_seconds=duration,
                extraction_results=extraction_results
            )
            
        except Exception as e:
            logger.error(f"Content extraction failed: {str(e)}", exc_info=True)
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return ContentExtractionResult(
                success=False,
                curriculum_id=request.curriculum_id,
                error_message=str(e),
                duration_seconds=duration
            )
    
    async def _get_sources(
        self,
        request: ContentExtractionRequest
    ) -> List[SourceExtractionTask]:
        """
        Get sources to extract from database
        
        Args:
            request: Extraction request
            
        Returns:
            List of source extraction tasks
        """
        # Get source records from database
        source_records = await self.source_repo.find_by_curriculum_id(
            request.curriculum_id
        )
        
        # Filter by specific source IDs if provided
        if request.source_ids:
            source_records = [
                s for s in source_records
                if s.source_id in request.source_ids
            ]
        
        # Limit if max_sources specified
        if request.max_sources:
            source_records = source_records[:request.max_sources]
        
        # Convert to extraction tasks
        tasks = []
        for source in source_records:
            task = SourceExtractionTask(
                source_id=source.source_id,
                url=source.url,
                content_format=source.content_metadata.format if source.content_metadata else "UNKNOWN",
                topic_ids=source.topic_ids,
                objective_ids=source.objective_ids
            )
            tasks.append(task)
        
        return tasks
    
    async def _extract_from_sources(
        self,
        sources: List[SourceExtractionTask]
    ) -> List[SourceExtractionResult]:
        """
        Extract content from multiple sources
        
        Args:
            sources: List of source extraction tasks
            
        Returns:
            List of extraction results
        """
        # Process sources sequentially to avoid rate limits
        # TODO: Could parallelize with semaphore
        results = []
        
        for i, source in enumerate(sources):
            logger.info(f"Processing source {i+1}/{len(sources)}: {source.source_id}")
            
            result = await self._extract_from_single_source(source)
            results.append(result)
            
            # Rate limiting
            if i < len(sources) - 1:
                await asyncio.sleep(2)
        
        return results
    
    async def _extract_from_single_source(
        self,
        source_task: SourceExtractionTask
    ) -> SourceExtractionResult:
        """
        Extract content from a single source
        
        Args:
            source_task: Source extraction task
            
        Returns:
            SourceExtractionResult
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Extract raw content
            logger.info(f"Extracting content from: {source_task.url}")
            
            extractor = self._get_extractor(source_task.url, source_task.content_format)
            
            if not extractor:
                logger.warning(f"No extractor found for {source_task.content_format}")
                return SourceExtractionResult(
                    source_id=source_task.source_id,
                    success=False,
                    error_message=f"No extractor for format: {source_task.content_format}"
                )
            
            extracted = await extractor.extract(source_task.url, source_task.source_id)
            
            if not extracted:
                return SourceExtractionResult(
                    source_id=source_task.source_id,
                    success=False,
                    error_message="Content extraction failed"
                )
            
            # Step 2: Chunk content
            logger.info(f"Chunking content...")
            
            chunks = self.chunking_service.chunk_content(
                extracted=extracted,
                topic_id=source_task.topic_ids[0] if source_task.topic_ids else "unknown",
                objective_ids=source_task.objective_ids
            )
            
            if not chunks:
                logger.warning("No chunks created")
                return SourceExtractionResult(
                    source_id=source_task.source_id,
                    success=False,
                    error_message="Chunking produced no results"
                )
            
            # Step 3: Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.generate_embeddings_batch(chunk_texts)
            
            # Step 4: Save knowledge chunks to database
            logger.info(f"Saving knowledge chunks to database...")
            
            for chunk, embedding in zip(chunks, embeddings):
                # Create knowledge chunk model
                chunk_model = KnowledgeChunkModel(
                    chunk_id=chunk.chunk_id,
                    scope=ChunkScope.TEMPLATE,
                    topic_id=chunk.topic_id,
                    objective_id=chunk.objective_id,
                    chunk_type=chunk.chunk_type,
                    content=chunk.content,
                    embedding=embedding,
                    tags=chunk.tags,
                    skill_tags=chunk.skill_tags,
                    difficulty=chunk.difficulty,
                    source={
                        "source_type": "OER",
                        "source_id": source_task.source_id,
                        "source_url": source_task.url,
                        "extracted_at": extracted.extracted_at
                    }
                )
                
                # Save to database
                await self.chunk_repo.create(chunk_model)
            
            # Update source record with created chunk IDs
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            await self.source_repo.update_created_chunks(
                source_task.source_id,
                chunk_ids
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Source complete: {len(chunks)} chunks in {duration:.2f}s")
            
            return SourceExtractionResult(
                source_id=source_task.source_id,
                success=True,
                chunks_created=len(chunks),
                extraction_time_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Source extraction failed: {str(e)}", exc_info=True)
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return SourceExtractionResult(
                source_id=source_task.source_id,
                success=False,
                error_message=str(e),
                extraction_time_seconds=duration
            )
    
    def _get_extractor(self, url: str, content_format: str):
        """Get appropriate extractor for URL/format"""
        for extractor in self.extractors:
            if extractor.can_extract(url, content_format):
                return extractor
        return None

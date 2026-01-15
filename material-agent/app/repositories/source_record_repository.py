"""
Repository for SourceRecord MongoDB operations
"""
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.models.source_record import SourceRecordModel

logger = logging.getLogger(__name__)


class SourceRecordRepository:
    """Repository for source record CRUD operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db['source_records']
    
    async def create(self, source_record: SourceRecordModel) -> SourceRecordModel:
        """Create a new source record"""
        doc = source_record.model_dump(by_alias=True, exclude_none=True)
        result = await self.collection.insert_one(doc)
        source_record.id = result.inserted_id
        logger.info(f"Created source record: {source_record.source_id}")
        return source_record
    
    async def find_by_curriculum_id(self, curriculum_id: str) -> List[SourceRecordModel]:
        """Find all sources for a curriculum"""
        cursor = self.collection.find({"curriculum_id": curriculum_id, "deleted": False})
        docs = await cursor.to_list(length=None)
        return [SourceRecordModel(**doc) for doc in docs]
    
    async def find_by_source_id(self, source_id: str) -> Optional[SourceRecordModel]:
        """Find source by ID"""
        doc = await self.collection.find_one({"source_id": source_id, "deleted": False})
        return SourceRecordModel(**doc) if doc else None
    
    async def create_indexes(self):
        """Create database indexes"""
        await self.collection.create_index("source_id", unique=True)
        await self.collection.create_index("curriculum_id")
        await self.collection.create_index("url", unique=True)
        await self.collection.create_index([("scoring.total", -1)])
        logger.info("Created source_records indexes")

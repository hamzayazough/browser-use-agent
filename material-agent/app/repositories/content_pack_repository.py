"""
Repository layer for ContentPack CRUD operations
"""
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.models import ContentPackModel


class ContentPackRepository:
    """Data access layer for content packs"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.content_packs
        
    async def create_indexes(self):
        """Create database indexes for optimal query performance"""
        await self.collection.create_index("pack_id", unique=True)
        await self.collection.create_index([("country", 1), ("region", 1), ("grade", 1), ("subject", 1)])
        await self.collection.create_index("status")
        await self.collection.create_index("published_at")
    
    async def create(self, pack: ContentPackModel) -> ContentPackModel:
        """Insert a new content pack"""
        pack_dict = pack.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(pack_dict)
        pack.id = str(result.inserted_id)
        return pack
    
    async def find_by_pack_id(self, pack_id: str) -> Optional[ContentPackModel]:
        """Find a pack by its unique pack_id"""
        doc = await self.collection.find_one({"pack_id": pack_id})
        if doc:
            return ContentPackModel(**doc)
        return None
    
    async def find_by_curriculum(
        self, 
        country: str, 
        grade: str, 
        subject: str,
        region: Optional[str] = None
    ) -> Optional[ContentPackModel]:
        """Find a content pack for specific curriculum parameters"""
        query = {
            "country": country,
            "grade": grade,
            "subject": subject,
            "status": "PUBLISHED"
        }
        if region:
            query["region"] = region
        
        doc = await self.collection.find_one(query, sort=[("published_at", -1)])  # Get latest version
        if doc:
            return ContentPackModel(**doc)
        return None
    
    async def list_packs(
        self,
        country: Optional[str] = None,
        grade: Optional[str] = None,
        subject: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ContentPackModel]:
        """List content packs with optional filtering"""
        query: Dict[str, Any] = {"status": "PUBLISHED"}
        
        if country:
            query["country"] = country
        if grade:
            query["grade"] = grade
        if subject:
            query["subject"] = subject
        
        cursor = self.collection.find(query).sort("published_at", -1).skip(skip).limit(limit)
        packs = []
        async for doc in cursor:
            packs.append(ContentPackModel(**doc))
        return packs
    
    async def update(self, pack_id: str, update_data: Dict[str, Any]) -> Optional[ContentPackModel]:
        """Update a content pack"""
        result = await self.collection.find_one_and_update(
            {"pack_id": pack_id},
            {"$set": update_data},
            return_document=True
        )
        if result:
            return ContentPackModel(**result)
        return None
    
    async def count_packs(self, country: Optional[str] = None) -> int:
        """Count total content packs"""
        query = {"status": "PUBLISHED"}
        if country:
            query["country"] = country
        return await self.collection.count_documents(query)

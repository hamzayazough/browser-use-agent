"""
Repository for managing cached known OER sources
"""
import logging
from typing import List, Optional
from datetime import datetime

from app.models.known_source import KnownSource

logger = logging.getLogger(__name__)


class KnownSourceRepository:
    """Repository for known OER sources"""
    
    def __init__(self, db):
        """
        Initialize repository
        
        Args:
            db: MongoDB database connection
        """
        self.collection = db["known_sources"]
    
    async def create(self, source: KnownSource) -> KnownSource:
        """
        Create a new known source
        
        Args:
            source: KnownSource model
            
        Returns:
            Created source
        """
        source_dict = source.model_dump()
        await self.collection.insert_one(source_dict)
        logger.info(f"Created known source: {source.source_key}")
        return source
    
    async def find_by_location(
        self,
        country: str,
        region: Optional[str] = None,
        subject: Optional[str] = None,
        grade: Optional[str] = None
    ) -> List[KnownSource]:
        """
        Find known sources by location and filters
        
        Args:
            country: Country code
            region: Optional region code
            subject: Optional subject filter
            grade: Optional grade level
            
        Returns:
            List of matching known sources
        """
        query = {
            "country": country,
            "is_active": True
        }
        
        # Add optional filters
        if region:
            # Match sources for specific region OR sources that work nationally
            query["$or"] = [
                {"region": region},
                {"region": None}
            ]
        
        if subject:
            query["subjects"] = {"$in": [subject]}
        
        # TODO: Add grade range filtering logic if needed
        
        cursor = self.collection.find(query)
        sources = []
        
        async for doc in cursor:
            try:
                sources.append(KnownSource(**doc))
            except Exception as e:
                logger.error(f"Failed to parse known source: {e}")
        
        logger.info(f"Found {len(sources)} known sources for {country}/{region}/{subject}")
        return sources
    
    async def find_by_key(self, source_key: str) -> Optional[KnownSource]:
        """
        Find known source by key
        
        Args:
            source_key: Unique source key
            
        Returns:
            KnownSource or None
        """
        doc = await self.collection.find_one({"source_key": source_key})
        if doc:
            return KnownSource(**doc)
        return None
    
    async def update_verification_date(self, source_key: str):
        """
        Update last verification date
        
        Args:
            source_key: Source key to update
        """
        await self.collection.update_one(
            {"source_key": source_key},
            {
                "$set": {
                    "last_verified": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def deactivate(self, source_key: str):
        """
        Deactivate a known source
        
        Args:
            source_key: Source key to deactivate
        """
        await self.collection.update_one(
            {"source_key": source_key},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Deactivated known source: {source_key}")
    
    async def bulk_create(self, sources: List[KnownSource]):
        """
        Bulk create known sources
        
        Args:
            sources: List of KnownSource models
        """
        if not sources:
            return
        
        source_dicts = [source.model_dump() for source in sources]
        await self.collection.insert_many(source_dicts)
        logger.info(f"Bulk created {len(sources)} known sources")

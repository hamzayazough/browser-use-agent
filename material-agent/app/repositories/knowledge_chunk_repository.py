"""
Repository layer for KnowledgeChunk CRUD operations
"""
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.models import KnowledgeChunkModel


class KnowledgeChunkRepository:
    """Data access layer for knowledge chunks"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.knowledge_chunks
        
    async def create_indexes(self):
        """Create database indexes for optimal query performance"""
        await self.collection.create_index("chunk_id", unique=True)
        await self.collection.create_index("topic_id")
        await self.collection.create_index("scope")
        await self.collection.create_index("instance_id")
        await self.collection.create_index("template_chunk_id")
        await self.collection.create_index("deleted")
        await self.collection.create_index([("tags", 1)])
        await self.collection.create_index([("embedding", "2dsphere")])  # For vector search
    
    async def create(self, chunk: KnowledgeChunkModel) -> KnowledgeChunkModel:
        """Insert a new knowledge chunk"""
        chunk_dict = chunk.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(chunk_dict)
        chunk.id = str(result.inserted_id)
        return chunk
    
    async def find_by_chunk_id(self, chunk_id: str) -> Optional[KnowledgeChunkModel]:
        """Find a chunk by its unique chunk_id"""
        doc = await self.collection.find_one({"chunk_id": chunk_id, "deleted": False})
        if doc:
            return KnowledgeChunkModel(**doc)
        return None
    
    async def find_by_topic(self, topic_id: str, scope: Optional[str] = None) -> List[KnowledgeChunkModel]:
        """Find all chunks for a specific topic"""
        query = {"topic_id": topic_id, "deleted": False}
        if scope:
            query["scope"] = scope
        
        cursor = self.collection.find(query)
        chunks = []
        async for doc in cursor:
            chunks.append(KnowledgeChunkModel(**doc))
        return chunks
    
    async def find_by_instance(self, instance_id: str) -> List[KnowledgeChunkModel]:
        """Find all instance-scoped chunks for a learning instance"""
        cursor = self.collection.find({
            "instance_id": instance_id,
            "scope": "INSTANCE",
            "deleted": False
        })
        chunks = []
        async for doc in cursor:
            chunks.append(KnowledgeChunkModel(**doc))
        return chunks
    
    async def update(self, chunk_id: str, update_data: Dict[str, Any]) -> Optional[KnowledgeChunkModel]:
        """Update a knowledge chunk"""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.find_one_and_update(
            {"chunk_id": chunk_id, "deleted": False},
            {"$set": update_data},
            return_document=True
        )
        if result:
            return KnowledgeChunkModel(**result)
        return None
    
    async def soft_delete(self, chunk_id: str) -> bool:
        """Soft delete a chunk (mark as deleted)"""
        result = await self.collection.update_one(
            {"chunk_id": chunk_id},
            {"$set": {"deleted": True, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def find_similar_by_embedding(
        self, 
        embedding: List[float], 
        topic_id: Optional[str] = None,
        limit: int = 10
    ) -> List[tuple[KnowledgeChunkModel, float]]:
        """
        Find similar chunks using vector similarity search
        Returns list of (chunk, similarity_score) tuples
        """
        query = {"deleted": False}
        if topic_id:
            query["topic_id"] = topic_id
        
        # MongoDB vector search aggregation pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "embedding_index",
                    "path": "embedding",
                    "queryVector": embedding,
                    "numCandidates": limit * 10,
                    "limit": limit
                }
            },
            {"$match": query},
            {
                "$addFields": {
                    "similarity_score": {"$meta": "searchScore"}
                }
            }
        ]
        
        cursor = self.collection.aggregate(pipeline)
        results = []
        async for doc in cursor:
            score = doc.pop("similarity_score", 0.0)
            results.append((KnowledgeChunkModel(**doc), score))
        
        return results
    
    async def bulk_create(self, chunks: List[KnowledgeChunkModel]) -> List[str]:
        """Insert multiple chunks in a single operation"""
        if not chunks:
            return []
        
        chunk_dicts = [chunk.model_dump(by_alias=True, exclude={"id"}) for chunk in chunks]
        result = await self.collection.insert_many(chunk_dicts)
        return [str(oid) for oid in result.inserted_ids]

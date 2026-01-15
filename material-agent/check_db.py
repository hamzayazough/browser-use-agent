"""
Quick script to check MongoDB data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_db():
    client = AsyncIOMotorClient("mongodb://admin:admin123@localhost:27017")
    db = client.tutorfroggy
    
    # Check curriculum IDs
    curriculum_ids = await db.source_records.distinct("curriculum_id")
    print(f"\n📚 Curriculum IDs in database: {curriculum_ids}")
    
    # Count sources
    source_count = await db.source_records.count_documents({})
    print(f"📄 Total source records: {source_count}")
    
    # Count chunks
    chunk_count = await db.knowledge_chunks.count_documents({})
    print(f"🧩 Total knowledge chunks: {chunk_count}")
    
    # Show sample source
    if source_count > 0:
        sample = await db.source_records.find_one()
        print(f"\n📋 Sample source:")
        print(f"  - source_id: {sample.get('source_id')}")
        print(f"  - curriculum_id: {sample.get('curriculum_id')}")
        print(f"  - url: {sample.get('url')}")
        print(f"  - title: {sample.get('title')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_db())

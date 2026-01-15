"""
Example: Test Curriculum Discovery Service

This script demonstrates how to use the Curriculum Discovery Service
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.curriculum_discovery import CurriculumDiscoveryRequest
from app.services.curriculum_discovery_service import CurriculumDiscoveryService
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def main():
    """Test the curriculum discovery service"""
    
    print("🚀 Testing Curriculum Discovery Service")
    print("=" * 50)
    
    # Connect to MongoDB
    print("\n📦 Connecting to MongoDB...")
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client.get_database()
    
    # Create service
    service = CurriculumDiscoveryService(
        db_connection=db,
        use_cloud=True  # Use Browser-Use cloud browser
    )
    
    # Create test request
    request = CurriculumDiscoveryRequest(
        country="US",
        region="CA",
        grade="4",
        subject="Mathematics",
        language="en"
    )
    
    print(f"\n📋 Discovery Request:")
    print(f"   Country: {request.country}")
    print(f"   Region: {request.region}")
    print(f"   Grade: {request.grade}")
    print(f"   Subject: {request.subject}")
    print(f"   Language: {request.language}")
    
    print("\n🔍 Starting curriculum discovery...")
    print("This may take 3-5 minutes...\n")
    
    # Run discovery
    result = await service.discover_curriculum(request)
    
    # Display results
    print("\n" + "=" * 50)
    if result.success:
        print("✅ Discovery Successful!")
        print(f"\n📊 Statistics:")
        print(f"   Curriculum ID: {result.curriculum_map.curriculum_id}")
        print(f"   Total Topics: {result.curriculum_map.statistics['total_topics']}")
        print(f"   Total Objectives: {result.curriculum_map.statistics['total_objectives']}")
        print(f"   Sources Discovered: {result.sources_discovered}")
        print(f"   Sources Vetted: {result.sources_vetted}")
        print(f"   Average Score: {result.curriculum_map.statistics['average_source_score']:.1f}")
        print(f"   Duration: {result.duration_seconds:.1f}s")
        
        print(f"\n📚 Vetted Sources:")
        for i, source in enumerate(result.curriculum_map.vetted_sources[:5], 1):
            print(f"   {i}. {source.title}")
            print(f"      Publisher: {source.publisher}")
            print(f"      Score: {source.scoring.total} | License: {source.license.value}")
            print(f"      URL: {source.url}")
    else:
        print(f"❌ Discovery Failed: {result.error_message}")
    
    # Close connection
    client.close()


if __name__ == "__main__":
    asyncio.run(main())

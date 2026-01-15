"""
Script to initialize known OER sources in MongoDB

Run this once to populate the database with cached known sources
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.services.known_source_service import KnownSourceService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialize known sources"""
    try:
        # Connect to database
        logger.info("Connecting to MongoDB...")
        await connect_to_mongo()
        
        # Get database
        db = await get_database()
        
        # Initialize service
        logger.info("Initializing known source service...")
        service = KnownSourceService(db)
        
        # Load default sources
        logger.info("Loading default known sources...")
        await service.initialize_default_sources()
        
        logger.info("✅ Successfully initialized known sources!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize known sources: {e}", exc_info=True)
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())

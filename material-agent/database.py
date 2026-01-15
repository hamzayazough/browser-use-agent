"""
Database configuration and connection management
"""
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient = None
    db = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB"""
    logger.info("Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(settings.mongodb_uri)
    db.db = db.client.get_default_database()
    logger.info("Connected to MongoDB successfully")


async def close_mongo_connection():
    """Close MongoDB connection"""
    logger.info("Closing MongoDB connection...")
    db.client.close()
    logger.info("MongoDB connection closed")


def get_database():
    """Get database instance"""
    return db.db

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        raise RuntimeError("MongoDB client not initialised. Call connect() first.")
    return _client


def get_collection() -> AsyncIOMotorCollection:
    return get_client()[settings.mongo_db_name][settings.mongo_collection]


async def connect():
    global _client
    logger.info("Connecting to MongoDB…")
    _client = AsyncIOMotorClient(settings.mongo_uri)
    # Verify connection
    await _client.admin.command("ping")
    logger.info(f"MongoDB connected → {settings.mongo_db_name}.{settings.mongo_collection}")


async def disconnect():
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("MongoDB disconnected.")

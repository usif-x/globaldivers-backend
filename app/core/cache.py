import logging
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.inmemory import InMemoryBackend
from redis import asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

async def init_cache():
    try:
        redis = aioredis.from_url(
            str(settings.DB_REDIS_URI),
            encoding="utf8",
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        
        # Test the connection
        await redis.ping()
        
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        logger.info("Successfully connected to Redis cache.")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis cache: {e}. Falling back to in-memory cache.")
        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")


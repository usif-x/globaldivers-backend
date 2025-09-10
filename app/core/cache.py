from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from app.core.config import settings


async def init_cache():
    redis = aioredis.from_url(
        str(settings.DB_REDIS_URI),  # 👈 نحولها لسترينج
        encoding="utf8",
        decode_responses=False
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

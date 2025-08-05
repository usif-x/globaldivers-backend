import os

from dotenv import load_dotenv
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

load_dotenv()

REDIS_URL = os.environ.get("REDIS_URI_TWO")


async def init_cache():
    redis = aioredis.from_url(REDIS_URL, encoding="utf8", decode_responses=False)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=str(settings.DB_REDIS_URI),
    default_limits=["100/minute"],
)

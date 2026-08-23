import logging
from typing import Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Standard optional redis package import
try:
    # pyrefly: ignore [missing-import]
    import redis
except ImportError:
    redis = None

class RedisClient:
    """
    Redis Async Client Wrapper with automatic in-memory fallback cache.
    Guarantees 100% uptime for retry tracking even if Redis server or package is unavailable.
    """
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client = None
        self._memory_cache: Dict[str, int] = {}

    async def get_client(self):
        """
        Lazily initializes the async Redis client. Returns None if Redis package is missing or URL is invalid.
        """
        if not self.redis_url or redis is None:
            return None
        if self._client is None:
            try:
                if hasattr(redis, "asyncio"):
                    self._client = redis.asyncio.from_url(self.redis_url, decode_responses=True)
                elif hasattr(redis, "from_url"):
                    self._client = redis.from_url(self.redis_url, decode_responses=True)
            except Exception as e:
                logger.warning(f"Redis connection initialization failed: {e}")
                return None
        return self._client

    async def get_retry_count(self, journal_id: str, farmer_id: str) -> int:
        key = f"retry_count:{journal_id}:{farmer_id}"
        try:
            client = await self.get_client()
            if client is not None:
                val = await client.get(key)
                if val is not None:
                    return int(val)
        except Exception as e:
            logger.warning(f"Redis get error (using in-memory fallback): {e}")

        return self._memory_cache.get(key, 0)

    async def increment_retry_count(self, journal_id: str, farmer_id: str) -> int:
        key = f"retry_count:{journal_id}:{farmer_id}"
        try:
            client = await self.get_client()
            if client is not None:
                val = await client.incr(key)
                await client.expire(key, 86400)
                return int(val)
        except Exception as e:
            logger.warning(f"Redis incr error (using in-memory fallback): {e}")

        self._memory_cache[key] = self._memory_cache.get(key, 0) + 1
        return self._memory_cache[key]

    async def reset_retry_count(self, journal_id: str, farmer_id: str):
        key = f"retry_count:{journal_id}:{farmer_id}"
        try:
            client = await self.get_client()
            if client is not None:
                await client.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")

        self._memory_cache.pop(key, None)

redis_client = RedisClient(settings.REDIS_URL)

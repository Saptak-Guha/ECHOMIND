"""
EchoMind Redis Connection
Redis client for caching, sessions, and real-time features.
"""

import json
from typing import Any, Optional
import redis.asyncio as aioredis
from redis.exceptions import RedisError
from app.core.config import settings


class RedisClient:
    """Async Redis client wrapper for EchoMind."""

    def __init__(self):
        self.client: Optional[aioredis.Redis] = None

    async def connect(self):
        """Initialize Redis connection."""
        self.client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        try:
            await self.client.ping()  # from_url is lazy; ping so startup reports the truth
        except Exception:
            self.client = None
            raise

    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()

    # ponytail: cache is optional — every primitive degrades to a miss when Redis
    # is down so the app still serves. Drop these guards if Redis becomes required.
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key. Returns None if Redis is unavailable."""
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except (RedisError, OSError):
            return None

    async def set(self, key: str, value: str, expire: int = 3600) -> None:
        """Set a key-value pair with optional expiration in seconds."""
        if not self.client:
            return
        try:
            await self.client.set(key, value, ex=expire)
        except (RedisError, OSError):
            pass

    async def delete(self, key: str) -> None:
        """Delete a key."""
        if not self.client:
            return
        try:
            await self.client.delete(key)
        except (RedisError, OSError):
            pass

    async def get_json(self, key: str) -> Optional[dict]:
        """Get a JSON value by key."""
        data = await self.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_json(self, key: str, value: Any, expire: int = 3600) -> None:
        """Set a JSON value."""
        await self.set(key, json.dumps(value), expire)

    async def cache_personality(self, user_id: str, profile: dict, expire: int = 1800) -> None:
        """Cache a personality profile for fast retrieval."""
        key = f"personality:{user_id}"
        await self.set_json(key, profile, expire)

    async def get_cached_personality(self, user_id: str) -> Optional[dict]:
        """Retrieve cached personality profile."""
        key = f"personality:{user_id}"
        return await self.get_json(key)

    async def cache_twin_context(self, user_id: str, context: dict, expire: int = 900) -> None:
        """Cache twin conversation context."""
        key = f"twin_context:{user_id}"
        await self.set_json(key, context, expire)

    async def get_twin_context(self, user_id: str) -> Optional[dict]:
        """Get cached twin context."""
        key = f"twin_context:{user_id}"
        return await self.get_json(key)

    async def increment_metric(self, metric_key: str) -> int:
        """Increment an analytics metric counter. Returns 0 if Redis is unavailable."""
        if not self.client:
            return 0
        try:
            return await self.client.incr(f"metric:{metric_key}")
        except (RedisError, OSError):
            return 0


redis_client = RedisClient()

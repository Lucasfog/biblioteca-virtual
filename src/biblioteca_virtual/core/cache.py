import json
from typing import Any, Optional

import redis.asyncio as redis


redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client


async def init_redis(url: str) -> redis.Redis:
    global redis_client
    redis_client = redis.from_url(url, encoding="utf-8", decode_responses=True)
    await redis_client.ping()
    return redis_client


async def close_redis() -> None:
    if redis_client is not None:
        await redis_client.close()


class Cache:
    def __init__(self, client: redis.Redis) -> None:
        self.client = client

    async def get_json(self, key: str) -> Any:
        value = await self.client.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        await self.client.set(key, json.dumps(value), ex=ttl_seconds)

    async def delete_pattern(self, pattern: str) -> int:
        deleted = 0
        async for key in self.client.scan_iter(match=pattern):
            await self.client.delete(key)
            deleted += 1
        return deleted

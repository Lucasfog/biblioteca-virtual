import json
from typing import Any, Optional

import redis.asyncio as redis


redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    if redis_client is None:
        # Return a no-op redis-compatible object to allow running without Redis (e.g. tests)
        class _Noop:
            async def ping(self):
                return True

            async def get(self, key):
                return None

            async def set(self, key, value, ex=None):
                return None

            async def delete(self, key):
                return None

            async def close(self):
                return None

            async def scan_iter(self, match=None):
                if False:
                    yield None

        return _Noop()
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

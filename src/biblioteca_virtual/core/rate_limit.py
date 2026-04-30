from fastapi import Request, Response
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from biblioteca_virtual.core.config import get_settings


async def init_rate_limiter(redis_client) -> None:
    await FastAPILimiter.init(redis_client)


def rate_limit_dependency(times: int, seconds: int):
    limiter = RateLimiter(times=times, seconds=seconds)

    async def dependency(request: Request, response: Response):
        settings = get_settings()
        if not settings.rate_limit_enabled or not settings.redis_enabled:
            return
        await limiter(request, response)

    return dependency

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.core.cache import get_redis
from biblioteca_virtual.core.config import get_settings
from biblioteca_virtual.core.db import get_session

health_router = APIRouter(tags=["Health"])


async def check_db(session: AsyncSession) -> bool:
    await session.execute(text("SELECT 1"))
    return True


async def check_redis() -> bool:
    redis = get_redis()
    await redis.ping()
    return True


@health_router.get("/health", summary="Health check")
async def health(session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    db_ok = await check_db(session)
    redis_ok = None

    if settings.redis_enabled:
        redis_ok = await check_redis()

    status = "ok" if db_ok and (redis_ok in (None, True)) else "degraded"
    return {"status": status, "db": db_ok, "redis": redis_ok}

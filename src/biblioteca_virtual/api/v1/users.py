from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.core.cache import Cache, get_redis
from biblioteca_virtual.core.config import get_settings
from biblioteca_virtual.core.db import get_session
from biblioteca_virtual.core.rate_limit import rate_limit_dependency
from biblioteca_virtual.core.security import get_current_user
from biblioteca_virtual.modules.users.schemas import UserCreate, UserRead
from biblioteca_virtual.modules.users.service import UserService
from biblioteca_virtual.modules.loans.schemas import LoanRead
from biblioteca_virtual.shared.pagination import PaginatedResponse, PaginationParams

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/users")


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


@router.get(
    "",
    response_model=PaginatedResponse[UserRead],
    summary="Listar usuarios",
    dependencies=[Depends(rate_limit_dependency(times=60, seconds=60))],
)
async def list_users(
    pagination: PaginationParams = Depends(),
    service: UserService = Depends(get_user_service),
    _current_user=Depends(get_current_user),
):
    settings = get_settings()
    cache_hit = False
    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"users:list:{pagination.offset}:{pagination.limit}"
        cached = await cache.get_json(cache_key)
        if cached is not None:
            logger.info("cache_hit", key=cache_key, entity="users")
            return cached
        logger.info("cache_miss", key=cache_key, entity="users")

    users, total = await service.list_users(pagination.offset, pagination.limit)
    validated_users = [UserRead.model_validate(u) for u in users]
    payload = PaginatedResponse.build(validated_users, total, pagination)

    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"users:list:{pagination.offset}:{pagination.limit}"
        await cache.set_json(cache_key, payload.model_dump(mode="json"), ttl_seconds=settings.cache_ttl_seconds)

    logger.info("users_listed", offset=pagination.offset, limit=pagination.limit, total=total, cache_hit=cache_hit)
    return payload


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar usuario",
    dependencies=[Depends(rate_limit_dependency(times=10, seconds=60))],
)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
):
    user = await service.create_user(payload)
    settings = get_settings()
    if settings.redis_enabled:
        cache = Cache(get_redis())
        await cache.delete_pattern("users:list:*")
    logger.info("user_created", user_id=str(user.id), email=user.email)
    return user


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Buscar usuario por ID",
    dependencies=[Depends(rate_limit_dependency(times=60, seconds=60))],
)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    _current_user=Depends(get_current_user),
):
    user = await service.get_user(user_id)
    logger.info("user_retrieved", user_id=str(user_id))
    return user


@router.get(
    "/{user_id}/loans",
    response_model=PaginatedResponse[LoanRead],
    summary="Historico de emprestimos de um usuario",
    dependencies=[Depends(rate_limit_dependency(times=60, seconds=60))],
)
async def list_user_loans(
    user_id: UUID,
    pagination: PaginationParams = Depends(),
    service: UserService = Depends(get_user_service),
    _current_user=Depends(get_current_user),
):
    settings = get_settings()
    cache_hit = False
    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"users:{user_id}:loans:{pagination.offset}:{pagination.limit}"
        cached = await cache.get_json(cache_key)
        if cached is not None:
            logger.info("cache_hit", key=cache_key, entity="user_loans")
            return cached
        logger.info("cache_miss", key=cache_key, entity="user_loans")

    loans, total = await service.list_user_loans(user_id, pagination.offset, pagination.limit)
    validated_loans = [LoanRead.model_validate(l) for l in loans]
    payload = PaginatedResponse.build(validated_loans, total, pagination)

    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"users:{user_id}:loans:{pagination.offset}:{pagination.limit}"
        await cache.set_json(cache_key, payload.model_dump(mode="json"), ttl_seconds=settings.cache_ttl_seconds)

    logger.info("user_loans_listed", user_id=str(user_id), offset=pagination.offset, limit=pagination.limit, total=total, cache_hit=cache_hit)
    return payload

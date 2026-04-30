import structlog
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.core.cache import Cache, get_redis
from biblioteca_virtual.core.config import get_settings
from biblioteca_virtual.core.db import get_session
from biblioteca_virtual.core.rate_limit import rate_limit_dependency
from biblioteca_virtual.core.security import get_current_user
from biblioteca_virtual.modules.loans.schemas import LoanCreate, LoanRead
from biblioteca_virtual.modules.loans.service import LoanService
from biblioteca_virtual.shared.pagination import PaginatedResponse, PaginationParams

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/loans")


def get_loan_service(session: AsyncSession = Depends(get_session)) -> LoanService:
    return LoanService(session)


@router.post(
    "",
    response_model=LoanRead,
    status_code=status.HTTP_201_CREATED,
    summary="Realizar emprestimo",
    dependencies=[Depends(rate_limit_dependency(times=10, seconds=60))],
)
async def create_loan(
    payload: LoanCreate,
    service: LoanService = Depends(get_loan_service),
    current_user=Depends(get_current_user),
):
    loan = await service.create_loan(payload)
    settings = get_settings()
    if settings.redis_enabled:
        cache = Cache(get_redis())
        await cache.delete_pattern("loans:*")
        await cache.delete_pattern("users:*:loans:*")
        await cache.delete_pattern("books:available:*")
    logger.info(
        "loan_created",
        loan_id=str(loan.id),
        user_id=str(payload.user_id),
        book_id=str(payload.book_id),
    )
    return loan


@router.post(
    "/{loan_id}/return",
    response_model=LoanRead,
    summary="Processar devolucao com multa",
    dependencies=[Depends(rate_limit_dependency(times=10, seconds=60))],
)
async def return_loan(
    loan_id: UUID,
    service: LoanService = Depends(get_loan_service),
    current_user=Depends(get_current_user),
):
    loan = await service.return_loan(loan_id)
    settings = get_settings()
    if settings.redis_enabled:
        cache = Cache(get_redis())
        await cache.delete_pattern("loans:*")
        await cache.delete_pattern("users:*:loans:*")
    fine_applied = loan.fine_cents > 0
    logger.info(
        "loan_returned",
        loan_id=str(loan_id),
        fine_cents=loan.fine_cents,
        fine_applied=fine_applied,
    )
    return loan


@router.get(
    "/active",
    response_model=PaginatedResponse[LoanRead],
    summary="Listar emprestimos ativos",
    dependencies=[Depends(rate_limit_dependency(times=60, seconds=60))],
)
async def list_active_loans(
    pagination: PaginationParams = Depends(),
    service: LoanService = Depends(get_loan_service),
    _current_user=Depends(get_current_user),
):
    settings = get_settings()
    cache_hit = False
    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"loans:active:{pagination.offset}:{pagination.limit}"
        cached = await cache.get_json(cache_key)
        if cached is not None:
            logger.info("cache_hit", key=cache_key, entity="loans_active")
            return cached
        logger.info("cache_miss", key=cache_key, entity="loans_active")

    loans, total = await service.list_active_loans(pagination.offset, pagination.limit)
    validated_loans = [LoanRead.model_validate(l) for l in loans]
    payload = PaginatedResponse.build(validated_loans, total, pagination)

    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"loans:active:{pagination.offset}:{pagination.limit}"
        await cache.set_json(cache_key, payload.model_dump(mode="json"), ttl_seconds=settings.cache_ttl_seconds)

    logger.info("active_loans_listed", offset=pagination.offset, limit=pagination.limit, total=total, cache_hit=cache_hit)
    return payload


@router.get(
    "/overdue",
    response_model=PaginatedResponse[LoanRead],
    summary="Listar emprestimos atrasados",
    dependencies=[Depends(rate_limit_dependency(times=60, seconds=60))],
)
async def list_overdue_loans(
    pagination: PaginationParams = Depends(),
    service: LoanService = Depends(get_loan_service),
    _current_user=Depends(get_current_user),
):
    settings = get_settings()
    cache_hit = False
    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"loans:overdue:{pagination.offset}:{pagination.limit}"
        cached = await cache.get_json(cache_key)
        if cached is not None:
            logger.info("cache_hit", key=cache_key, entity="loans_overdue")
            return cached
        logger.info("cache_miss", key=cache_key, entity="loans_overdue")

    loans, total = await service.list_overdue_loans(pagination.offset, pagination.limit)
    validated_loans = [LoanRead.model_validate(l) for l in loans]
    payload = PaginatedResponse.build(validated_loans, total, pagination)

    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"loans:overdue:{pagination.offset}:{pagination.limit}"
        await cache.set_json(cache_key, payload.model_dump(mode="json"), ttl_seconds=settings.cache_ttl_seconds)

    logger.info("overdue_loans_listed", offset=pagination.offset, limit=pagination.limit, total=total, cache_hit=cache_hit)
    return payload


@router.get(
    "/user/{user_id}",
    response_model=PaginatedResponse[LoanRead],
    summary="Historico de emprestimos por usuario",
    dependencies=[Depends(rate_limit_dependency(times=60, seconds=60))],
)
async def list_user_history(
    user_id: UUID,
    pagination: PaginationParams = Depends(),
    service: LoanService = Depends(get_loan_service),
    _current_user=Depends(get_current_user),
):
    settings = get_settings()
    cache_hit = False
    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"loans:user:{user_id}:{pagination.offset}:{pagination.limit}"
        cached = await cache.get_json(cache_key)
        if cached is not None:
            logger.info("cache_hit", key=cache_key, entity="loans_user")
            return cached
        logger.info("cache_miss", key=cache_key, entity="loans_user")

    loans, total = await service.list_user_loans(user_id, pagination.offset, pagination.limit)
    validated_loans = [LoanRead.model_validate(l) for l in loans]
    payload = PaginatedResponse.build(validated_loans, total, pagination)

    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"loans:user:{user_id}:{pagination.offset}:{pagination.limit}"
        await cache.set_json(cache_key, payload.model_dump(mode="json"), ttl_seconds=settings.cache_ttl_seconds)

    logger.info("user_history_listed", user_id=str(user_id), offset=pagination.offset, limit=pagination.limit, total=total, cache_hit=cache_hit)
    return payload

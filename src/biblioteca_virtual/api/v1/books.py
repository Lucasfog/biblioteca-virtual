import structlog
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.core.cache import Cache, get_redis
from biblioteca_virtual.core.config import get_settings, Settings
from biblioteca_virtual.core.db import get_session
from biblioteca_virtual.core.rate_limit import rate_limit_dependency
from biblioteca_virtual.core.security import get_current_user
from biblioteca_virtual.modules.books.schemas import (
    BookAvailability,
    BookCreate,
    BookRead,
)
from biblioteca_virtual.modules.books.service import BookService
from biblioteca_virtual.shared.pagination import PaginatedResponse, PaginationParams

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/books")


def get_book_service(session: AsyncSession = Depends(get_session)) -> BookService:
    return BookService(session)


@router.get(
    "",
    response_model=PaginatedResponse[BookRead],
    summary="Listar livros",
    dependencies=[Depends(rate_limit_dependency(times=60, seconds=60))],
)
async def list_books(
    pagination: PaginationParams = Depends(),
    service: BookService = Depends(get_book_service),
    _current_user=Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    cache_hit = False
    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"books:list:{pagination.offset}:{pagination.limit}"
        cached = await cache.get_json(cache_key)
        if cached is not None:
            logger.info("cache_hit", key=cache_key, entity="books")
            return cached
        logger.info("cache_miss", key=cache_key, entity="books")
        cache_hit = False

    books, total = await service.list_books(pagination.offset, pagination.limit)
    validated_books = [BookRead.model_validate(b) for b in books]
    payload = PaginatedResponse.build(validated_books, total, pagination)

    if settings.redis_enabled:
        cache = Cache(get_redis())
        cache_key = f"books:list:{pagination.offset}:{pagination.limit}"
        await cache.set_json(cache_key, payload.model_dump(mode="json"), ttl_seconds=settings.cache_ttl_seconds)

    logger.info(
        "books_listed",
        offset=pagination.offset,
        limit=pagination.limit,
        total=total,
        cache_hit=cache_hit,
    )
    return payload


@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar livro vinculado a autor",
    dependencies=[Depends(rate_limit_dependency(times=10, seconds=60))],
)
async def create_book(
    payload: BookCreate,
    service: BookService = Depends(get_book_service),
    _current_user=Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    book = await service.create_book(payload)
    if settings.redis_enabled:
        cache = Cache(get_redis())
        await cache.delete_pattern("books:list:*")
        await cache.delete_pattern("books:available:*")
    logger.info("book_created", book_id=str(book.id), isbn=book.isbn)
    return book


@router.get(
    "/{book_id}/availability",
    response_model=BookAvailability,
    summary="Verificar disponibilidade",
    dependencies=[Depends(rate_limit_dependency(times=60, seconds=60))],
)
async def check_availability(
    book_id: UUID,
    service: BookService = Depends(get_book_service),
    _current_user=Depends(get_current_user),
):
    availability = await service.get_availability(book_id)
    logger.info("book_availability_checked", book_id=str(book_id), available=availability.is_available)
    return availability

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from biblioteca_virtual.modules.books.models import Author, Book


class BookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, offset: int, limit: int) -> list[Book]:
        result = await self.session.execute(
            select(Book)
            .options(selectinload(Book.author))
            .order_by(Book.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(Book))
        return int(result.scalar_one())

    async def count_available(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Book).where(Book.available_copies > 0)
        )
        return int(result.scalar_one())

    async def get_by_id(self, book_id: UUID) -> Book | None:
        result = await self.session.execute(
            select(Book).options(selectinload(Book.author)).where(Book.id == book_id)
        )
        return result.scalar_one_or_none()

    async def get_by_isbn(self, isbn: str) -> Book | None:
        result = await self.session.execute(select(Book).where(Book.isbn == isbn))
        return result.scalar_one_or_none()

    async def get_for_update(self, book_id: UUID) -> Book | None:
        result = await self.session.execute(
            select(Book).where(Book.id == book_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_author_by_name(self, name: str) -> Author | None:
        result = await self.session.execute(
            select(Author).where(func.lower(Author.name) == name.lower())
        )
        return result.scalar_one_or_none()

    def add(self, entity) -> None:
        self.session.add(entity)

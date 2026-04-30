import structlog
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.core.db import transaction
from biblioteca_virtual.core.errors import ConflictError, NotFoundError
from biblioteca_virtual.modules.books.models import Author, Book
from biblioteca_virtual.modules.books.repository import BookRepository
from biblioteca_virtual.modules.books.schemas import BookAvailability, BookCreate

logger = structlog.get_logger(__name__)


class BookService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.books = BookRepository(session)

    async def list_books(self, offset: int, limit: int) -> tuple[list[Book], int]:
        books, total = await self.books.list(offset, limit), await self.books.count()
        logger.info("books_service_list", offset=offset, limit=limit, total=total)
        return books, total

    async def count_available_books(self) -> int:
        return await self.books.count_available()

    async def create_book(self, payload: BookCreate) -> Book:
        async with transaction(self.session):
            existing = await self.books.get_by_isbn(payload.isbn)
            if existing is not None:
                logger.warning("book_create_failed_isbn_exists", isbn=payload.isbn)
                raise ConflictError("ISBN ja cadastrado")

            author = await self.books.get_author_by_name(payload.author_name)
            if author is None:
                author = Author(name=payload.author_name)
                self.books.add(author)

            book = Book(
                title=payload.title,
                isbn=payload.isbn,
                total_copies=payload.total_copies,
                available_copies=payload.total_copies,
                author=author,
            )
            self.books.add(book)
            await self.session.flush()
            book_id = book.id

        if book_id is None:
            raise NotFoundError("Livro nao encontrado")

        loaded = await self.books.get_by_id(book_id)
        if loaded is None:
            raise NotFoundError("Livro nao encontrado")
        logger.info("book_service_created", book_id=str(book.id), isbn=book.isbn)
        return loaded

    async def get_availability(self, book_id: UUID) -> BookAvailability:
        book = await self.books.get_by_id(book_id)
        if book is None:
            logger.warning("book_not_found", book_id=str(book_id))
            raise NotFoundError("Livro nao encontrado")
        logger.info("book_availability_checked", book_id=str(book_id), available=book.available_copies)
        return BookAvailability(
            book_id=book.id,
            available_copies=book.available_copies,
            is_available=book.available_copies > 0,
        )

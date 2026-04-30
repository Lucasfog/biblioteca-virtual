import asyncio

from biblioteca_virtual.core.db import get_session_maker
from biblioteca_virtual.core.security import get_password_hash
from biblioteca_virtual.modules.books.models import Author, Book
from biblioteca_virtual.modules.books.repository import BookRepository
from biblioteca_virtual.modules.users.models import User
from biblioteca_virtual.modules.users.repository import UserRepository
from biblioteca_virtual.modules.loans.models import Loan


async def seed() -> None:
    session_maker = get_session_maker()
    async with session_maker() as session:
        users = UserRepository(session)
        books = BookRepository(session)

        async with session.begin():
            existing = await users.get_by_email("admin@biblioteca.com")
            if existing is None:
                admin = User(
                    full_name="Admin Biblioteca",
                    email="admin@biblioteca.com",
                    hashed_password=get_password_hash("Admin123!"),
                )
                users.add(admin)

            author = await books.get_author_by_name("Machado de Assis")
            if author is None:
                author = Author(name="Machado de Assis")
                books.add(author)

            if await books.get_by_isbn("9780000000001") is None:
                book = Book(
                    title="Dom Casmurro",
                    isbn="9780000000001",
                    total_copies=5,
                    available_copies=5,
                    author=author,
                )
                books.add(book)

            if await books.get_by_isbn("9780000000002") is None:
                book = Book(
                    title="Memorias Postumas de Bras Cubas",
                    isbn="9780000000002",
                    total_copies=3,
                    available_copies=3,
                    author=author,
                )
                books.add(book)


if __name__ == "__main__":
    asyncio.run(seed())

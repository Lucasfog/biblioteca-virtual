from datetime import timedelta

import pytest

from biblioteca_virtual.core.constants import FINE_PER_DAY_CENTS
from biblioteca_virtual.core.errors import BusinessRuleError
from biblioteca_virtual.core.security import get_password_hash
from biblioteca_virtual.modules.books.models import Author, Book
from biblioteca_virtual.modules.loans.schemas import LoanCreate
from biblioteca_virtual.modules.loans.service import LoanService
from biblioteca_virtual.modules.users.models import User
from biblioteca_virtual.shared.utils import utcnow


@pytest.mark.asyncio
async def test_max_active_loans(async_session):
    user = User(
        full_name="Maria Silva",
        email="maria@example.com",
        hashed_password=get_password_hash("Senha123!"),
    )
    author = Author(name="Autor 1")
    book = Book(
        title="Livro 1",
        isbn="9780000000001",
        total_copies=5,
        available_copies=5,
        author=author,
    )
    async_session.add_all([user, book])
    await async_session.commit()

    service = LoanService(async_session)

    for _ in range(3):
        await service.create_loan(LoanCreate(user_id=user.id, book_id=book.id))

    with pytest.raises(BusinessRuleError):
        await service.create_loan(LoanCreate(user_id=user.id, book_id=book.id))


@pytest.mark.asyncio
async def test_return_loan_calculates_fine(async_session):
    user = User(
        full_name="Carlos Souza",
        email="carlos@example.com",
        hashed_password=get_password_hash("Senha123!"),
    )
    author = Author(name="Autor 2")
    book = Book(
        title="Livro 2",
        isbn="9780000000002",
        total_copies=1,
        available_copies=1,
        author=author,
    )
    async_session.add_all([user, book])
    await async_session.commit()

    service = LoanService(async_session)
    loan = await service.create_loan(LoanCreate(user_id=user.id, book_id=book.id))

    loan.due_at = utcnow() - timedelta(days=3)
    await async_session.commit()

    updated = await service.return_loan(loan.id)

    assert updated.fine_cents == 3 * FINE_PER_DAY_CENTS
    await async_session.refresh(book)
    assert book.available_copies == 1

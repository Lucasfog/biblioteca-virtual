"""Testes unitários para services - regras de negócio"""
from datetime import timedelta
from uuid import uuid4

import pytest

from biblioteca_virtual.core.constants import FINE_PER_DAY_CENTS, MAX_ACTIVE_LOANS
from biblioteca_virtual.core.errors import BusinessRuleError, ConflictError, NotFoundError
from biblioteca_virtual.core.security import get_password_hash
from biblioteca_virtual.modules.books.models import Author, Book
from biblioteca_virtual.modules.books.service import BookService
from biblioteca_virtual.modules.loans.models import LoanStatus
from biblioteca_virtual.modules.loans.schemas import LoanCreate
from biblioteca_virtual.modules.loans.service import LoanService
from biblioteca_virtual.modules.users.models import User
from biblioteca_virtual.modules.users.schemas import UserCreate
from biblioteca_virtual.modules.users.service import UserService
from biblioteca_virtual.shared.utils import utcnow


class TestLoanServiceBusinessRules:
    """Testes unitários para LoanService"""

    @pytest.mark.asyncio
    async def test_max_active_loans_per_user(self, async_session):
        """Usuário não pode exceder MAX_ACTIVE_LOANS (3) empréstimos ativos"""
        user = User(
            full_name="Maria Silva",
            email="maria@example.com",
            hashed_password=get_password_hash("Senha123!"),
        )
        author = Author(name="Autor Teste")
        book = Book(
            title="Livro Teste",
            isbn="9780000000001",
            total_copies=10,
            available_copies=10,
            author=author,
        )
        async_session.add_all([user, author, book])
        await async_session.commit()

        service = LoanService(async_session)

        for i in range(MAX_ACTIVE_LOANS):
            await service.create_loan(LoanCreate(user_id=user.id, book_id=book.id))

        with pytest.raises(BusinessRuleError, match="excedeu limite"):
            await service.create_loan(LoanCreate(user_id=user.id, book_id=book.id))

    @pytest.mark.asyncio
    async def test_loan_unavailable_book(self, async_session):
        """Não é possível emprestar livro sem cópias disponíveis"""
        user = User(
            full_name="João Santos",
            email="joao@example.com",
            hashed_password=get_password_hash("Senha123!"),
        )
        author = Author(name="Autor X")
        book = Book(
            title="Livro Único",
            isbn="9780000000002",
            total_copies=1,
            available_copies=0,
            author=author,
        )
        async_session.add_all([user, author, book])
        await async_session.commit()

        service = LoanService(async_session)

        with pytest.raises(BusinessRuleError, match="sem disponibilidade"):
            await service.create_loan(LoanCreate(user_id=user.id, book_id=book.id))

    @pytest.mark.asyncio
    async def test_return_loan_no_fine_on_time(self, async_session):
        """Devolução dentro do prazo não gera multa"""
        user = User(
            full_name="Ana Costa",
            email="ana@example.com",
            hashed_password=get_password_hash("Senha123!"),
        )
        author = Author(name="Autor Y")
        book = Book(
            title="Livro Prazo",
            isbn="9780000000003",
            total_copies=1,
            available_copies=1,
            author=author,
        )
        async_session.add_all([user, author, book])
        await async_session.commit()

        service = LoanService(async_session)
        loan = await service.create_loan(LoanCreate(user_id=user.id, book_id=book.id))

        loan.due_at = utcnow() + timedelta(days=7)
        await async_session.commit()

        returned = await service.return_loan(loan.id)
        assert returned.fine_cents == 0
        assert returned.status == LoanStatus.RETURNED

    @pytest.mark.asyncio
    async def test_return_loan_with_fine(self, async_session):
        """Devolução atrasada gera multa proporcional aos dias"""
        user = User(
            full_name="Pedro Oliveira",
            email="pedro@example.com",
            hashed_password=get_password_hash("Senha123!"),
        )
        author = Author(name="Autor Z")
        book = Book(
            title="Livro Multa",
            isbn="9780000000004",
            total_copies=1,
            available_copies=1,
            author=author,
        )
        async_session.add_all([user, author, book])
        await async_session.commit()

        service = LoanService(async_session)
        loan = await service.create_loan(LoanCreate(user_id=user.id, book_id=book.id))

        days_late = 5
        loan.due_at = utcnow() - timedelta(days=days_late)
        await async_session.commit()

        returned = await service.return_loan(loan.id)
        expected_fine = days_late * FINE_PER_DAY_CENTS
        assert returned.fine_cents == expected_fine

    @pytest.mark.asyncio
    async def test_return_already_returned_loan(self, async_session):
        """Não é possível devolver empréstimo já retornado"""
        user = User(
            full_name="Lucas Ferreira",
            email="lucas@example.com",
            hashed_password=get_password_hash("Senha123!"),
        )
        author = Author(name="Autor W")
        book = Book(
            title="Livro Retornado",
            isbn="9780000000005",
            total_copies=1,
            available_copies=1,
            author=author,
        )
        async_session.add_all([user, author, book])
        await async_session.commit()

        service = LoanService(async_session)
        loan = await service.create_loan(LoanCreate(user_id=user.id, book_id=book.id))

        await service.return_loan(loan.id)

        with pytest.raises(BusinessRuleError, match="ja devolvido"):
            await service.return_loan(loan.id)

    @pytest.mark.asyncio
    async def test_loan_nonexistent_user(self, async_session):
        """Tentativa de empréstimo com usuário inexistente falha"""
        author = Author(name="Autor A")
        book = Book(
            title="Livro A",
            isbn="9780000000006",
            total_copies=5,
            available_copies=5,
            author=author,
        )
        async_session.add(author, book)
        await async_session.commit()

        service = LoanService(async_session)
        fake_user_id = uuid4()

        with pytest.raises(NotFoundError, match="Usuario nao encontrado"):
            await service.create_loan(LoanCreate(user_id=fake_user_id, book_id=book.id))

    @pytest.mark.asyncio
    async def test_loan_nonexistent_book(self, async_session):
        """Tentativa de empréstimo com livro inexistente falha"""
        user = User(
            full_name="Beatriz Lima",
            email="bia@example.com",
            hashed_password=get_password_hash("Senha123!"),
        )
        async_session.add(user)
        await async_session.commit()

        service = LoanService(async_session)
        fake_book_id = uuid4()

        with pytest.raises(NotFoundError, match="Livro nao encontrado"):
            await service.create_loan(LoanCreate(user_id=user.id, book_id=fake_book_id))


class TestUserService:
    """Testes unitários para UserService"""

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, async_session):
        """Não é possível criar usuário com email duplicado"""
        user = User(
            full_name="Primeiro Usuario",
            email="duplicate@example.com",
            hashed_password=get_password_hash("Senha123!"),
        )
        async_session.add(user)
        await async_session.commit()

        service = UserService(async_session)
        payload = UserCreate(
            full_name="Segundo Usuario",
            email="duplicate@example.com",
            password="Senha456!",
        )

        with pytest.raises(ConflictError, match="Email ja cadastrado"):
            await service.create_user(payload)

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, async_session):
        """Buscar usuário inexistente lança NotFoundError"""
        service = UserService(async_session)
        fake_id = uuid4()

        with pytest.raises(NotFoundError, match="Usuario nao encontrado"):
            await service.get_user(fake_id)


class TestBookService:
    """Testes unitários para BookService"""

    @pytest.mark.asyncio
    async def test_create_book_duplicate_isbn(self, async_session):
        """Não é possível criar livro com ISBN duplicado"""
        author = Author(name="Autor ISBN")
        book = Book(
            title="Livro ISBN Duplicado",
            isbn="9780000000010",
            total_copies=5,
            available_copies=5,
            author=author,
        )
        async_session.add_all([author, book])
        await async_session.commit()

        service = BookService(async_session)
        from biblioteca_virtual.modules.books.schemas import BookCreate

        payload = BookCreate(
            title="Outro Livro",
            isbn="9780000000010",
            author_name="Outro Autor",
            total_copies=3,
        )

        with pytest.raises(ConflictError, match="ISBN ja cadastrado"):
            await service.create_book(payload)

    @pytest.mark.asyncio
    async def test_get_availability_not_found(self, async_session):
        """Buscar disponibilidade de livro inexistente lança NotFoundError"""
        service = BookService(async_session)
        fake_id = uuid4()

        with pytest.raises(NotFoundError, match="Livro nao encontrado"):
            await service.get_availability(fake_id)


class TestFineCalculation:
    """Testes para cálculo de multa"""

    def test_fine_zero_days_late(self):
        """Multa zero quando devolvido no prazo"""
        due_at = utcnow()
        returned_at = utcnow()
        fine = LoanService.calculate_fine_cents(due_at, returned_at)
        assert fine == 0

    def test_fine_five_days_late(self):
        """Multa correta para 5 dias de atraso"""
        due_at = utcnow() - timedelta(days=5)
        returned_at = utcnow()
        fine = LoanService.calculate_fine_cents(due_at, returned_at)
        assert fine == 5 * FINE_PER_DAY_CENTS

    def test_fine_partial_day_rounds_down(self):
        """Multa calculada por dias completos"""
        due_at = utcnow() - timedelta(days=2, hours=12)
        returned_at = utcnow()
        fine = LoanService.calculate_fine_cents(due_at, returned_at)
        assert fine == 2 * FINE_PER_DAY_CENTS

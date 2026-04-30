import structlog
from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.core.constants import (
    FINE_PER_DAY_CENTS,
    LOAN_TERM_DAYS,
    MAX_ACTIVE_LOANS,
)
from biblioteca_virtual.core.db import transaction
from biblioteca_virtual.core.errors import BusinessRuleError, NotFoundError
from biblioteca_virtual.modules.books.repository import BookRepository
from biblioteca_virtual.modules.loans.models import Loan, LoanStatus
from biblioteca_virtual.modules.loans.repository import LoanRepository
from biblioteca_virtual.modules.loans.schemas import LoanCreate
from biblioteca_virtual.modules.users.repository import UserRepository
from biblioteca_virtual.shared.utils import utcnow

logger = structlog.get_logger(__name__)


class LoanService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.loans = LoanRepository(session)
        self.users = UserRepository(session)
        self.books = BookRepository(session)

    async def create_loan(self, payload: LoanCreate) -> Loan:
        async with transaction(self.session):
            user = await self.users.get_by_id(payload.user_id)
            if user is None:
                logger.warning("loan_creation_user_not_found", user_id=str(payload.user_id))
                raise NotFoundError("Usuario nao encontrado")

            book = await self.books.get_for_update(payload.book_id)
            if book is None:
                logger.warning("loan_creation_book_not_found", book_id=str(payload.book_id))
                raise NotFoundError("Livro nao encontrado")

            active_count = await self.loans.count_active_by_user(payload.user_id)
            if active_count >= MAX_ACTIVE_LOANS:
                logger.warning(
                    "loan_creation_max_loans_exceeded",
                    user_id=str(payload.user_id),
                    active_count=active_count,
                )
                raise BusinessRuleError("Usuario excedeu limite de emprestimos ativos")

            if book.available_copies <= 0:
                logger.warning("loan_creation_book_unavailable", book_id=str(payload.book_id))
                raise BusinessRuleError("Livro sem disponibilidade")

            due_at = utcnow() + timedelta(days=LOAN_TERM_DAYS)
            loan = Loan(
                user_id=payload.user_id,
                book_id=payload.book_id,
                status=LoanStatus.ACTIVE,
                due_at=due_at,
            )
            book.available_copies -= 1
            self.loans.add(loan)

        await self.session.refresh(loan)
        logger.info(
            "loan_service_created",
            loan_id=str(loan.id),
            user_id=str(payload.user_id),
            book_id=str(payload.book_id),
        )
        return loan

    async def return_loan(self, loan_id: UUID) -> Loan:
        async with transaction(self.session):
            loan = await self.loans.get_by_id(loan_id, for_update=True)
            if loan is None:
                logger.warning("loan_return_not_found", loan_id=str(loan_id))
                raise NotFoundError("Emprestimo nao encontrado")
            if loan.status == LoanStatus.RETURNED:
                logger.warning("loan_return_already_returned", loan_id=str(loan_id))
                raise BusinessRuleError("Emprestimo ja devolvido")

            book = await self.books.get_for_update(loan.book_id)
            if book is None:
                logger.warning("loan_return_book_not_found", book_id=str(loan.book_id))
                raise NotFoundError("Livro nao encontrado")

            returned_at = utcnow()
            loan.returned_at = returned_at
            loan.status = LoanStatus.RETURNED
            loan.fine_cents = self.calculate_fine_cents(loan.due_at, returned_at)
            if book.available_copies >= book.total_copies:
                raise BusinessRuleError("Quantidade de copias inconsistente")
            book.available_copies += 1

        await self.session.refresh(loan)
        fine_applied = loan.fine_cents > 0
        if fine_applied:
            logger.info(
                "loan_service_returned_with_fine",
                loan_id=str(loan_id),
                fine_cents=loan.fine_cents,
            )
        else:
            logger.info("loan_service_returned", loan_id=str(loan_id))
        return loan

    async def list_active_loans(self, offset: int = 0, limit: int = 50) -> tuple[list[Loan], int]:
        loans, total = await self.loans.list_active(offset, limit), await self.loans.count_active()
        logger.info("loans_service_list_active", offset=offset, limit=limit, total=total)
        return loans, total

    async def list_overdue_loans(self, offset: int = 0, limit: int = 50) -> tuple[list[Loan], int]:
        loans, total = await self.loans.list_overdue(offset, limit), await self.loans.count_overdue()
        logger.info("loans_service_list_overdue", offset=offset, limit=limit, total=total)
        return loans, total

    async def list_user_loans(self, user_id: UUID, offset: int = 0, limit: int = 50) -> tuple[list[Loan], int]:
        user = await self.users.get_by_id(user_id)
        if user is None:
            logger.warning("user_not_found_for_loans", user_id=str(user_id))
            raise NotFoundError("Usuario nao encontrado")
        loans, total = await self.loans.list_by_user(user_id, offset, limit), await self.loans.count_by_user(user_id)
        logger.info("loans_service_list_by_user", user_id=str(user_id), total=total)
        return loans, total

    @staticmethod
    def calculate_fine_cents(due_at, returned_at) -> int:
        if due_at.tzinfo is None and returned_at.tzinfo is not None:
            due_at = due_at.replace(tzinfo=returned_at.tzinfo)
        elif due_at.tzinfo is not None and returned_at.tzinfo is None:
            returned_at = returned_at.replace(tzinfo=due_at.tzinfo)

        if returned_at <= due_at:
            return 0
        late_days = (returned_at - due_at).days
        if late_days < 0:
            late_days = 0
        return late_days * FINE_PER_DAY_CENTS

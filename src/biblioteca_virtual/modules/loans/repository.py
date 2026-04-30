from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from biblioteca_virtual.modules.loans.models import Loan, LoanStatus
from biblioteca_virtual.shared.utils import utcnow


class LoanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, loan_id: UUID, for_update: bool = False) -> Loan | None:
        query = select(Loan).options(selectinload(Loan.book))
        if for_update:
            query = query.with_for_update()
        result = await self.session.execute(query.where(Loan.id == loan_id))
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID, offset: int = 0, limit: int = 50) -> list[Loan]:
        result = await self.session.execute(
            select(Loan)
            .where(Loan.user_id == user_id)
            .order_by(Loan.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Loan).where(Loan.user_id == user_id)
        )
        return int(result.scalar_one())

    async def list_active(self, offset: int = 0, limit: int = 50) -> list[Loan]:
        result = await self.session.execute(
            select(Loan)
            .where(Loan.status == LoanStatus.ACTIVE)
            .order_by(Loan.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_loans(self) -> list[Loan]:
        """Obtém TODOS os empréstimos ativos com relações carregadas (para scheduler)."""
        result = await self.session.execute(
            select(Loan)
            .where(Loan.status == LoanStatus.ACTIVE)
            .options(
                selectinload(Loan.book),
                selectinload(Loan.user),
            )
            .order_by(Loan.due_at.asc())
        )
        return list(result.scalars().unique().all())

    async def count_active(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Loan).where(Loan.status == LoanStatus.ACTIVE)
        )
        return int(result.scalar_one())

    async def list_overdue(self, offset: int = 0, limit: int = 50) -> list[Loan]:
        now = utcnow()
        result = await self.session.execute(
            select(Loan)
            .where(Loan.status == LoanStatus.ACTIVE)
            .where(Loan.due_at < now)
            .order_by(Loan.due_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_overdue(self) -> int:
        now = utcnow()
        result = await self.session.execute(
            select(func.count())
            .select_from(Loan)
            .where(Loan.status == LoanStatus.ACTIVE)
            .where(Loan.due_at < now)
        )
        return int(result.scalar_one())

    async def count_active_by_user(self, user_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Loan)
            .where(Loan.user_id == user_id)
            .where(Loan.status == LoanStatus.ACTIVE)
        )
        return int(result.scalar_one())

    async def count_active_by_book(self, book_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Loan)
            .where(Loan.book_id == book_id)
            .where(Loan.status == LoanStatus.ACTIVE)
        )
        return int(result.scalar_one())

    def add(self, loan: Loan) -> None:
        self.session.add(loan)

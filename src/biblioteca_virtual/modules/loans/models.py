import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, UUID, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from biblioteca_virtual.core.db import Base
from biblioteca_virtual.modules.books.models import Book
from biblioteca_virtual.modules.users.models import User

if TYPE_CHECKING:
    from biblioteca_virtual.modules.books.models import Book as BookType
    from biblioteca_virtual.modules.users.models import User as UserType


class LoanStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    book_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id"), index=True, nullable=False
    )
    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus), default=LoanStatus.ACTIVE, index=True, nullable=False
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fine_cents: Mapped[int | None] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["UserType"] = relationship("User", back_populates="loans")
    book: Mapped["BookType"] = relationship("Book", back_populates="loans")

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UUID, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from biblioteca_virtual.core.db import Base

if TYPE_CHECKING:
    from biblioteca_virtual.modules.loans.models import Loan


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(
        String(120), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    books: Mapped[list["Book"]] = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("total_copies >= 0"),
        CheckConstraint("available_copies >= 0"),
        CheckConstraint("available_copies <= total_copies"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    isbn: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    total_copies: Mapped[int] = mapped_column(Integer, nullable=False)
    available_copies: Mapped[int] = mapped_column(Integer, nullable=False)
    author_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("authors.id"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    author: Mapped[Author] = relationship("Author", back_populates="books")
    loans: Mapped[list["Loan"]] = relationship("Loan", back_populates="book")

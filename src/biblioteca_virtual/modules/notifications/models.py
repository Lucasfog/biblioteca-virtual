import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UUID, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from biblioteca_virtual.core.db import Base

if TYPE_CHECKING:
    from biblioteca_virtual.modules.loans.models import Loan
    from biblioteca_virtual.modules.users.models import User


class NotificationType(str, enum.Enum):
    """Tipo de notificação de empréstimo."""

    DUE_SOON = "due_soon"  # Vencimento próximo
    OVERDUE = "overdue"  # Empréstimo vencido


class NotificationChannel(str, enum.Enum):
    """Canal de entrega de notificação."""

    EMAIL = "email"
    WEBHOOK = "webhook"


class NotificationStatus(str, enum.Enum):
    """Status de envio de notificação."""

    PENDING = "pending"  # Aguardando envio
    SENT = "sent"  # Enviado com sucesso
    FAILED = "failed"  # Falha no envio


class LoanNotification(Base):
    """
    Rastreamento de notificações de empréstimos.
    
    Armazena histórico de notificações enviadas para evitar duplicação
    e rastrear status de envios.
    """

    __tablename__ = "loan_notifications"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    loan_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loans.id"), index=True, nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        String(50), nullable=False
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        String(50), nullable=False
    )
    status: Mapped[NotificationStatus] = mapped_column(
        String(50), default=NotificationStatus.PENDING, index=True, nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    loan: Mapped["Loan"] = relationship("Loan")
    user: Mapped["User"] = relationship("User")

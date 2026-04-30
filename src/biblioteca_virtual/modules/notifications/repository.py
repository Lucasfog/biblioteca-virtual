from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.modules.notifications.models import (
    LoanNotification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)


class NotificationRepository:
    """Repositório para operações com notificações."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, notification: LoanNotification) -> None:
        """Adiciona notificação para persistência."""
        self.session.add(notification)

    async def get_by_id(self, notification_id: UUID) -> LoanNotification | None:
        """Obtém notificação por ID."""
        query = select(LoanNotification).where(LoanNotification.id == notification_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save(self, notification: LoanNotification) -> None:
        """Persiste alterações de notificação."""
        await self.session.flush()
        await self.session.refresh(notification)

    async def check_notification_sent(
        self,
        loan_id: UUID,
        notification_type: NotificationType,
        channel: NotificationChannel,
    ) -> bool:
        """
        Verifica se uma notificação de um tipo específico foi enviada para um empréstimo.
        
        Busca notificações com status SENT ou PENDING para evitar duplicatas.
        """
        query = select(func.count(LoanNotification.id)).where(
            and_(
                LoanNotification.loan_id == loan_id,
                LoanNotification.type == notification_type,
                LoanNotification.channel == channel,
                LoanNotification.status.in_(
                    [NotificationStatus.SENT, NotificationStatus.PENDING]
                ),
            )
        )
        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0

    async def get_pending_notifications(
        self, limit: int = 100
    ) -> list[LoanNotification]:
        """Obtém notificações pendentes de envio."""
        query = (
            select(LoanNotification)
            .where(LoanNotification.status == NotificationStatus.PENDING)
            .order_by(LoanNotification.created_at)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_failed_notifications_for_retry(
        self, max_retries: int = 3, hours_since_failure: int = 1
    ) -> list[LoanNotification]:
        """
        Obtém notificações com falha que são elegíveis para retry.
        
        Args:
            max_retries: Número máximo de tentativas
            hours_since_failure: Horas mínimas desde a falha
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_since_failure)

        query = (
            select(LoanNotification)
            .where(
                and_(
                    LoanNotification.status == NotificationStatus.FAILED,
                    LoanNotification.created_at <= cutoff_time,
                )
            )
            .order_by(LoanNotification.created_at)
            .limit(100)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_sent_by_loan(
        self,
        loan_id: UUID,
        days: int = 7,
    ) -> int:
        """Conta notificações enviadas para um empréstimo nos últimos N dias."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        query = select(func.count(LoanNotification.id)).where(
            and_(
                LoanNotification.loan_id == loan_id,
                LoanNotification.status == NotificationStatus.SENT,
                LoanNotification.created_at >= cutoff_time,
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_recent_notifications(
        self,
        loan_id: UUID,
        notification_type: NotificationType,
        days: int = 1,
    ) -> list[LoanNotification]:
        """Obtém notificações recentes de um tipo específico para um empréstimo."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        query = (
            select(LoanNotification)
            .where(
                and_(
                    LoanNotification.loan_id == loan_id,
                    LoanNotification.type == notification_type,
                    LoanNotification.created_at >= cutoff_time,
                )
            )
            .order_by(desc(LoanNotification.created_at))
        )
        result = await self.session.execute(query)
        return result.scalars().all()

"""
Serviço principal de notificações de empréstimos.

Orquestra envio de notificações por email e webhook,
evita duplicação e gerencia o histórico de notificações.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.modules.loans.models import Loan, LoanStatus
from biblioteca_virtual.modules.loans.repository import LoanRepository
from biblioteca_virtual.modules.notifications.email import (
    EmailNotificationService,
)
from biblioteca_virtual.modules.notifications.models import (
    LoanNotification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from biblioteca_virtual.modules.notifications.repository import NotificationRepository
from biblioteca_virtual.modules.notifications.webhook import (
    WebhookNotificationService,
)
from biblioteca_virtual.modules.users.repository import UserRepository
from biblioteca_virtual.shared.utils import utcnow

logger = structlog.get_logger(__name__)


class NotificationService:
    """
    Serviço centralizado para gerenciamento de notificações de empréstimos.
    
    Responsabilidades:
    - Determinar quando notificar (próximo vencimento / atraso)
    - Evitar notificações duplicadas
    - Rastrear histórico de notificações
    - Enviar por múltiplos canais (email, webhook)
    - Registrar logs estruturados
    """

    def __init__(
        self,
        session: AsyncSession,
        email_service: Optional[EmailNotificationService] = None,
        webhook_service: Optional[WebhookNotificationService] = None,
    ):
        self.session = session
        self.email_service = email_service
        self.webhook_service = webhook_service
        
        self.loans_repo = LoanRepository(session)
        self.users_repo = UserRepository(session)
        self.notifications_repo = NotificationRepository(session)

    async def process_loan_notifications(self) -> None:
        """
        Processa todos os empréstimos ativos e dispara notificações conforme necessário.
        
        Chamado periodicament pelo scheduler (1x por dia ou por hora).
        """
        logger.info("notification_processing_started")
        
        # Obtém todos os empréstimos ativos
        active_loans = await self.loans_repo.get_active_loans()
        
        for loan in active_loans:
            try:
                await self._process_single_loan(loan)
            except Exception as e:
                logger.error(
                    "notification_processing_error",
                    loan_id=str(loan.id),
                    error=str(e),
                )

        logger.info("notification_processing_completed")

    async def _process_single_loan(self, loan: Loan) -> None:
        """Processa notificações para um empréstimo específico."""
        current_time = utcnow()
        days_remaining = self._calculate_days_remaining(loan.due_at, current_time)
        
        user = await self.users_repo.get_by_id(loan.user_id)
        if not user:
            logger.warning("notification_user_not_found", user_id=str(loan.user_id))
            return

        book = loan.book
        if not book:
            logger.warning("notification_book_not_found", book_id=str(loan.book_id))
            return

        # Determina tipo de notificação
        if days_remaining > 0:
            # Vencimento próximo
            await self._send_due_soon_notifications(
                loan=loan,
                user=user,
                book=book,
                days_left=days_remaining,
            )
        else:
            # Vencimento passou (atraso)
            await self._send_overdue_notifications(
                loan=loan,
                user=user,
                book=book,
                days_overdue=abs(days_remaining),
            )

    async def _send_due_soon_notifications(
        self,
        loan: Loan,
        user,
        book,
        days_left: int,
    ) -> None:
        """Envia notificações de vencimento próximo."""
        notification_type = NotificationType.DUE_SOON

        # Email
        if self.email_service:
            already_sent = await self.notifications_repo.check_notification_sent(
                loan_id=loan.id,
                notification_type=notification_type,
                channel=NotificationChannel.EMAIL,
            )

            if not already_sent:
                success = await self.email_service.send_due_soon_notification(
                    to_email=user.email,
                    user_name=user.full_name,
                    book_title=book.title,
                    due_date=loan.due_at,
                    days_left=days_left,
                )

                await self._record_notification(
                    loan_id=loan.id,
                    user_id=user.id,
                    notification_type=notification_type,
                    channel=NotificationChannel.EMAIL,
                    success=success,
                )

        # Webhook
        if self.webhook_service:
            # Aqui você poderia adicionar configuração de webhook por usuário
            # Para este exemplo, apenas log
            logger.debug("webhook_notification_skipped_no_url", loan_id=str(loan.id))

    async def _send_overdue_notifications(
        self,
        loan: Loan,
        user,
        book,
        days_overdue: int,
    ) -> None:
        """Envia notificações de empréstimo vencido."""
        notification_type = NotificationType.OVERDUE

        # Email (enviado diariamente enquanto vencido)
        if self.email_service:
            # Verifica se já foi notificado hoje
            recent = await self.notifications_repo.get_recent_notifications(
                loan_id=loan.id,
                notification_type=notification_type,
                days=1,
            )

            if not recent:  # Se não notificado hoje, envia
                success = await self.email_service.send_overdue_notification(
                    to_email=user.email,
                    user_name=user.full_name,
                    book_title=book.title,
                    due_date=loan.due_at,
                    days_overdue=days_overdue,
                )

                await self._record_notification(
                    loan_id=loan.id,
                    user_id=user.id,
                    notification_type=notification_type,
                    channel=NotificationChannel.EMAIL,
                    success=success,
                )

    async def _record_notification(
        self,
        loan_id: UUID,
        user_id: UUID,
        notification_type: NotificationType,
        channel: NotificationChannel,
        success: bool,
    ) -> None:
        """Registra uma notificação no banco de dados para rastreamento."""
        notification = LoanNotification(
            loan_id=loan_id,
            user_id=user_id,
            type=notification_type,
            channel=channel,
            status=NotificationStatus.SENT if success else NotificationStatus.FAILED,
            sent_at=utcnow() if success else None,
            error_message=None if success else "Send failed",
        )

        self.notifications_repo.add(notification)
        await self.notifications_repo.save(notification)

        log_level = "notification_sent" if success else "notification_failed"
        logger.info(
            log_level,
            loan_id=str(loan_id),
            user_id=str(user_id),
            type=notification_type.value,
            channel=channel.value,
        )

    @staticmethod
    def _calculate_days_remaining(due_at: datetime, current_time: datetime) -> int:
        """
        Calcula dias restantes até vencimento.
        
        Retorna:
        - Positivo: dias até vencimento
        - Negativo: dias em atraso
        - Zero: venceu hoje
        """
        delta = due_at - current_time
        return delta.days

    async def send_manual_notification(
        self,
        loan_id: UUID,
        notification_type: NotificationType,
        channels: list[NotificationChannel],
    ) -> bool:
        """
        Envia notificação manual para um empréstimo específico.
        
        Útil para testes e ações manuais do admin.
        """
        loan = await self.loans_repo.get_by_id(loan_id)
        if not loan:
            logger.warning("manual_notification_loan_not_found", loan_id=str(loan_id))
            return False

        user = await self.users_repo.get_by_id(loan.user_id)
        if not user:
            logger.warning("manual_notification_user_not_found", user_id=str(loan.user_id))
            return False

        book = loan.book
        if not book:
            logger.warning("manual_notification_book_not_found", book_id=str(loan.book_id))
            return False

        current_time = utcnow()
        days_remaining = self._calculate_days_remaining(loan.due_at, current_time)

        success = True

        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL and self.email_service:
                    if notification_type == NotificationType.DUE_SOON:
                        result = await self.email_service.send_due_soon_notification(
                            to_email=user.email,
                            user_name=user.full_name,
                            book_title=book.title,
                            due_date=loan.due_at,
                            days_left=max(0, days_remaining),
                        )
                    else:
                        result = await self.email_service.send_overdue_notification(
                            to_email=user.email,
                            user_name=user.full_name,
                            book_title=book.title,
                            due_date=loan.due_at,
                            days_overdue=max(0, abs(days_remaining)),
                        )
                    success = success and result

                await self._record_notification(
                    loan_id=loan.id,
                    user_id=user.id,
                    notification_type=notification_type,
                    channel=channel,
                    success=success,
                )

            except Exception as e:
                logger.error(
                    "manual_notification_error",
                    loan_id=str(loan_id),
                    channel=channel.value,
                    error=str(e),
                )
                success = False

        return success

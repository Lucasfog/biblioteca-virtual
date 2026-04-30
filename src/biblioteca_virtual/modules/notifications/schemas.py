from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from biblioteca_virtual.modules.notifications.models import (
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)


class LoanNotificationBase(BaseModel):
    """Base schema para notificações de empréstimo."""

    type: NotificationType
    channel: NotificationChannel
    status: NotificationStatus


class LoanNotificationCreate(BaseModel):
    """Schema para criação de notificação."""

    loan_id: UUID
    user_id: UUID
    type: NotificationType
    channel: NotificationChannel


class LoanNotificationUpdate(BaseModel):
    """Schema para atualização de notificação."""

    status: NotificationStatus
    sent_at: datetime | None = None
    error_message: str | None = None


class LoanNotificationResponse(LoanNotificationBase):
    """Schema de resposta de notificação."""

    id: UUID
    loan_id: UUID
    user_id: UUID
    sent_at: datetime | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationPayload(BaseModel):
    """Payload com informações de notificação para envio."""

    user_email: str
    user_name: str
    book_title: str
    due_date: datetime
    days_left: int
    loan_id: UUID
    is_overdue: bool


class WebhookPayload(BaseModel):
    """Payload para webhook de notificação."""

    event: str  # loan_due_soon | loan_overdue
    user_id: str
    loan_id: str
    book_title: str
    due_date: str
    days_left: int
    is_overdue: bool
    timestamp: str

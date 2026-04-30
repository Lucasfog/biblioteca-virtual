"""Módulo de notificações de empréstimos."""

from biblioteca_virtual.modules.notifications.email import (
    EmailNotificationService,
    EmailTemplateRenderer,
    EmailProvider,
    MockEmailProvider,
    SMTPEmailProvider,
)
from biblioteca_virtual.modules.notifications.models import (
    LoanNotification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from biblioteca_virtual.modules.notifications.repository import (
    NotificationRepository,
)
from biblioteca_virtual.modules.notifications.schemas import (
    LoanNotificationCreate,
    LoanNotificationResponse,
    LoanNotificationUpdate,
    NotificationPayload,
    WebhookPayload,
)
from biblioteca_virtual.modules.notifications.service import (
    NotificationService,
)
from biblioteca_virtual.modules.notifications.webhook import (
    HTTPWebhookProvider,
    MockWebhookProvider,
    WebhookNotificationService,
    WebhookProvider,
)

__all__ = [
    # Models
    "LoanNotification",
    "NotificationType",
    "NotificationChannel",
    "NotificationStatus",
    # Schemas
    "LoanNotificationCreate",
    "LoanNotificationResponse",
    "LoanNotificationUpdate",
    "NotificationPayload",
    "WebhookPayload",
    # Email
    "EmailProvider",
    "EmailNotificationService",
    "EmailTemplateRenderer",
    "MockEmailProvider",
    "SMTPEmailProvider",
    # Webhook
    "WebhookProvider",
    "WebhookNotificationService",
    "MockWebhookProvider",
    "HTTPWebhookProvider",
    # Service & Repository
    "NotificationService",
    "NotificationRepository",
]

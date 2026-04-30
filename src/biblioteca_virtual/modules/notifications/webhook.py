"""
Módulo para envio de notificações via webhook.

Suporta webhooks HTTP com retry automático e logging detalhado.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import httpx
import structlog

from biblioteca_virtual.modules.notifications.schemas import WebhookPayload

logger = structlog.get_logger(__name__)


class WebhookProvider(ABC):
    """Interface abstrata para provedores de webhook."""

    @abstractmethod
    async def send_webhook(
        self,
        webhook_url: str,
        payload: WebhookPayload,
    ) -> bool:
        """Envia webhook e retorna True se bem-sucedido."""
        pass


class MockWebhookProvider(WebhookProvider):
    """Provider mock para testes e desenvolvimento."""

    async def send_webhook(
        self,
        webhook_url: str,
        payload: WebhookPayload,
    ) -> bool:
        """Simula envio de webhook (apenas registra em log)."""
        logger.info(
            "mock_webhook_sent",
            webhook_url=webhook_url,
            event=payload.event,
            loan_id=payload.loan_id,
        )
        return True


class HTTPWebhookProvider(WebhookProvider):
    """Provider real usando HTTP POST."""

    def __init__(
        self,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        self.timeout = timeout
        self.max_retries = max_retries

    async def send_webhook(
        self,
        webhook_url: str,
        payload: WebhookPayload,
    ) -> bool:
        """Envia webhook via HTTP POST com retry."""
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        webhook_url,
                        json=payload.model_dump(),
                        timeout=self.timeout,
                    )

                    if response.status_code in (200, 201, 202):
                        logger.info(
                            "webhook_sent_success",
                            webhook_url=webhook_url,
                            event=payload.event,
                            status_code=response.status_code,
                        )
                        return True
                    else:
                        logger.warning(
                            "webhook_send_failed",
                            webhook_url=webhook_url,
                            event=payload.event,
                            status_code=response.status_code,
                            attempt=attempt + 1,
                        )

            except httpx.TimeoutException:
                logger.warning(
                    "webhook_timeout",
                    webhook_url=webhook_url,
                    event=payload.event,
                    attempt=attempt + 1,
                )
            except Exception as e:
                logger.error(
                    "webhook_send_error",
                    webhook_url=webhook_url,
                    event=payload.event,
                    error=str(e),
                    attempt=attempt + 1,
                )

        return False


class WebhookNotificationService:
    """Serviço para envio de notificações via webhook."""

    def __init__(self, provider: WebhookProvider):
        self.provider = provider

    async def send_loan_due_soon(
        self,
        webhook_url: str,
        user_id: str,
        loan_id: str,
        book_title: str,
        due_date: datetime,
        days_left: int,
    ) -> bool:
        """Envia notificação de vencimento próximo via webhook."""
        payload = WebhookPayload(
            event="loan_due_soon",
            user_id=user_id,
            loan_id=loan_id,
            book_title=book_title,
            due_date=due_date.isoformat(),
            days_left=days_left,
            is_overdue=False,
            timestamp=datetime.utcnow().isoformat(),
        )
        return await self.provider.send_webhook(webhook_url, payload)

    async def send_loan_overdue(
        self,
        webhook_url: str,
        user_id: str,
        loan_id: str,
        book_title: str,
        due_date: datetime,
        days_overdue: int,
    ) -> bool:
        """Envia notificação de empréstimo vencido via webhook."""
        payload = WebhookPayload(
            event="loan_overdue",
            user_id=user_id,
            loan_id=loan_id,
            book_title=book_title,
            due_date=due_date.isoformat(),
            days_left=-days_overdue,
            is_overdue=True,
            timestamp=datetime.utcnow().isoformat(),
        )
        return await self.provider.send_webhook(webhook_url, payload)

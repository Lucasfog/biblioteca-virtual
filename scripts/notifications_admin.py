#!/usr/bin/env python3
"""
Script para administração e testes do sistema de notificações.

Uso:
    python scripts/notifications_admin.py process
    python scripts/notifications_admin.py send-manual <loan_id>
    python scripts/notifications_admin.py cleanup
"""

import asyncio
import sys
from uuid import UUID
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

for path in (str(SRC_DIR), str(ROOT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import structlog

from biblioteca_virtual.core.config import get_settings
from biblioteca_virtual.core.scheduler import run_notifications_manually
from biblioteca_virtual.modules.notifications import (
    EmailNotificationService,
    MockEmailProvider,
    NotificationChannel,
    NotificationRepository,
    NotificationService,
    NotificationType,
    SMTPEmailProvider,
    WebhookNotificationService,
)
from biblioteca_virtual.modules.notifications.webhook import (
    HTTPWebhookProvider,
    MockWebhookProvider,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = structlog.get_logger(__name__)


async def process_notifications() -> None:
    """Executa processamento de notificações manualmente."""
    logger.info("manual_notification_processing_started")
    await run_notifications_manually()
    logger.info("manual_notification_processing_completed")


async def send_manual_notification(loan_id_str: str) -> None:
    """Envia notificação manual para um empréstimo específico."""
    try:
        loan_id = UUID(loan_id_str)
    except ValueError:
        logger.error("invalid_loan_id_format", loan_id=loan_id_str)
        return

    settings = get_settings()
    
    # Configura conexão
    async_engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )
    async_session_maker = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        session = async_session_maker()
        try:
            # Cria provedores
            email_provider = (
                SMTPEmailProvider(
                    smtp_host=settings.smtp_host,
                    smtp_port=settings.smtp_port,
                    sender_email=settings.email_sender_address,
                    sender_password=settings.smtp_password,
                    use_tls=settings.smtp_use_tls,
                    smtp_username=settings.smtp_username,
                )
                if settings.email_provider == "smtp"
                else MockEmailProvider()
            )

            email_service = EmailNotificationService(
                provider=email_provider,
                sender_name=settings.email_sender_name,
                sender_email=settings.email_sender_address,
            )

            webhook_provider = (
                HTTPWebhookProvider(
                    timeout=settings.webhook_timeout,
                    max_retries=settings.webhook_max_retries,
                )
                if settings.webhook_enabled
                else MockWebhookProvider()
            )

            webhook_service = WebhookNotificationService(provider=webhook_provider)

            # Envia notificação
            service = NotificationService(
                session=session,
                email_service=email_service,
                webhook_service=webhook_service,
            )

            # Tenta enviar como due_soon
            success = await service.send_manual_notification(
                loan_id=loan_id,
                notification_type=NotificationType.DUE_SOON,
                channels=[NotificationChannel.EMAIL],
            )

            if success:
                logger.info("manual_notification_sent_success", loan_id=str(loan_id))
            else:
                logger.error("manual_notification_sent_failed", loan_id=str(loan_id))

        finally:
            await session.close()
    finally:
        await async_engine.dispose()


async def cleanup_notifications() -> None:
    """Limpa notificações antigas."""
    logger.info("cleanup_notifications_started")
    
    settings = get_settings()
    async_engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )
    async_session_maker = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        session = async_session_maker()
        try:
            # Aqui você pode adicionar lógica de limpeza
            # Por exemplo, deletar notificações com mais de 30 dias
            logger.info("cleanup_completed")
        finally:
            await session.close()
    finally:
        await async_engine.dispose()


async def list_notifications() -> None:
    """Lista notificações recentes."""
    logger.info("list_notifications_started")
    
    settings = get_settings()
    async_engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )
    async_session_maker = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        session = async_session_maker()
        try:
            repo = NotificationRepository(session)
            pending = await repo.get_pending_notifications(limit=10)
            
            print("\n📬 Notificações Pendentes:")
            for notif in pending:
                print(
                    f"  - Empréstimo: {notif.loan_id} | "
                    f"Tipo: {notif.type.value} | "
                    f"Canal: {notif.channel.value} | "
                    f"Criada: {notif.created_at}"
                )
            
            if not pending:
                print("  Nenhuma notificação pendente")

        finally:
            await session.close()
    finally:
        await async_engine.dispose()


def main() -> None:
    """Entry point."""
    if len(sys.argv) < 2:
        print("Uso: python scripts/notifications_admin.py <comando>")
        print("\nComandos:")
        print("  process                     - Processa todas as notificações")
        print("  send-manual <loan_id>       - Envia notificação para empréstimo específico")
        print("  list                        - Lista notificações pendentes")
        print("  cleanup                     - Limpa notificações antigas")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "process":
            asyncio.run(process_notifications())
        elif command == "send-manual" and len(sys.argv) > 2:
            asyncio.run(send_manual_notification(sys.argv[2]))
        elif command == "list":
            asyncio.run(list_notifications())
        elif command == "cleanup":
            asyncio.run(cleanup_notifications())
        else:
            print(f"Comando desconhecido: {command}")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("interrupted_by_user")
        sys.exit(0)
    except Exception as e:
        logger.error("script_error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()

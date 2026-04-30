"""
Scheduler de notificações de empréstimos.

Utiliza APScheduler para disparar job de verificação de notificações periodicamente.
"""

from contextlib import asynccontextmanager
from datetime import datetime

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from biblioteca_virtual.core.config import Settings, get_settings
from biblioteca_virtual.modules.notifications import (
    EmailNotificationService,
    MockEmailProvider,
    NotificationService,
    SMTPEmailProvider,
    WebhookNotificationService,
)
from biblioteca_virtual.modules.notifications.webhook import (
    HTTPWebhookProvider,
    MockWebhookProvider,
)

logger = structlog.get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None
_async_engine = None
_async_session_maker = None


async def init_notification_scheduler(app) -> None:
    """Inicializa o scheduler de notificações."""
    global _scheduler, _async_engine, _async_session_maker

    settings = get_settings()

    if not settings.notification_enabled or not settings.notification_scheduler_enabled:
        logger.info("notification_scheduler_disabled")
        return

    logger.info(
        "notification_scheduler_initializing",
        interval_minutes=settings.notification_scheduler_interval_minutes,
    )

    # Inicializa sessão assíncrona
    _async_engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )
    _async_session_maker = sessionmaker(
        _async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Configura scheduler
    _scheduler = AsyncIOScheduler()

    # Registra job
    _scheduler.add_job(
        _run_notification_job,
        "interval",
        minutes=settings.notification_scheduler_interval_minutes,
        id="notification_job",
        name="Loan Notification Processor",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("notification_scheduler_started")


async def shutdown_notification_scheduler() -> None:
    """Encerra o scheduler de notificações."""
    global _scheduler, _async_engine

    if _scheduler:
        _scheduler.shutdown()
        logger.info("notification_scheduler_shutdown")

    if _async_engine:
        await _async_engine.dispose()


@asynccontextmanager
async def get_notification_session():
    """Context manager para obter sessão de banco."""
    if not _async_session_maker:
        raise RuntimeError("Scheduler not initialized")

    session = _async_session_maker()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error("notification_session_error", error=str(e))
        raise
    finally:
        await session.close()


async def _run_notification_job() -> None:
    """Job executado pelo scheduler para processar notificações."""
    try:
        logger.info("notification_job_started", timestamp=datetime.utcnow().isoformat())

        settings = get_settings()

        # Cria instâncias de provedores
        if settings.email_provider == "smtp":
            email_provider = SMTPEmailProvider(
                smtp_host=settings.smtp_host,
                smtp_port=settings.smtp_port,
                sender_email=settings.email_sender_address,
                sender_password=settings.smtp_password,
                use_tls=settings.smtp_use_tls,
                smtp_username=settings.smtp_username,
            )
        else:
            email_provider = MockEmailProvider()

        email_service = (
            EmailNotificationService(
                provider=email_provider,
                sender_name=settings.email_sender_name,
                sender_email=settings.email_sender_address,
            )
            if settings.notification_enabled
            else None
        )

        if settings.webhook_enabled:
            webhook_provider = HTTPWebhookProvider(
                timeout=settings.webhook_timeout,
                max_retries=settings.webhook_max_retries,
            )
        else:
            webhook_provider = MockWebhookProvider()

        webhook_service = (
            WebhookNotificationService(provider=webhook_provider)
            if settings.webhook_enabled
            else None
        )

        async with get_notification_session() as session:
            service = NotificationService(
                session=session,
                email_service=email_service,
                webhook_service=webhook_service,
            )

            await service.process_loan_notifications()

        logger.info(
            "notification_job_completed",
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(
            "notification_job_failed",
            error=str(e),
            timestamp=datetime.utcnow().isoformat(),
        )


# Função para execução manual (útil para CLI ou admin)
async def run_notifications_manually(settings: Settings | None = None) -> None:
    """
    Executa processamento de notificações manualmente.
    
    Útil para testes, CLI ou ajustes administrativos.
    """
    if settings is None:
        settings = get_settings()

    if settings.email_provider == "smtp":
        email_provider = SMTPEmailProvider(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            sender_email=settings.email_sender_address,
            sender_password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
            smtp_username=settings.smtp_username,
        )
    else:
        email_provider = MockEmailProvider()

    email_service = EmailNotificationService(
        provider=email_provider,
        sender_name=settings.email_sender_name,
        sender_email=settings.email_sender_address,
    )

    if settings.webhook_enabled:
        webhook_provider = HTTPWebhookProvider(
            timeout=settings.webhook_timeout,
            max_retries=settings.webhook_max_retries,
        )
        webhook_service = WebhookNotificationService(provider=webhook_provider)
    else:
        webhook_service = WebhookNotificationService(provider=MockWebhookProvider())

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
        async with async_session_maker() as session:
            try:
                service = NotificationService(
                    session=session,
                    email_service=email_service,
                    webhook_service=webhook_service,
                )

                await service.process_loan_notifications()
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error("manual_notification_failed", error=str(e))
                raise
    finally:
        await async_engine.dispose()

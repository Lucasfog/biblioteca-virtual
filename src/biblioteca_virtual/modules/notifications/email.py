"""
Módulo para envio de notificações por email.

Suporta templates HTML com Jinja2 e é facilmente mockável para testes.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from pathlib import Path
import ssl
import smtplib
from typing import Optional

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = structlog.get_logger(__name__)


class EmailProvider(ABC):
    """Interface abstrata para provedores de email."""

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """Envia email e retorna True se bem-sucedido."""
        pass


class MockEmailProvider(EmailProvider):
    """Provider mock para testes e desenvolvimento."""

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """Simula envio de email (apenas registra em log)."""
        logger.info(
            "mock_email_sent",
            to_email=to_email,
            subject=subject,
            preview=html_content[:100],
        )
        return True


class SMTPEmailProvider(EmailProvider):
    """Provider real usando SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        use_tls: bool = True,
        smtp_username: str | None = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls
        self.smtp_username = smtp_username or sender_email

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """Envia email via SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = Header(subject, "utf-8")
            msg["From"] = self.sender_email
            msg["To"] = to_email

            # Adiciona versão texto alternativa (fallback)
            text_content = self._html_to_text(html_content)
            part1 = MIMEText(text_content, "plain", "utf-8")
            part2 = MIMEText(html_content, "html", "utf-8")

            msg.attach(part1)
            msg.attach(part2)

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.ehlo()
                if self.use_tls:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                server.login(self.smtp_username, self.sender_password)
                server.send_message(msg)

            logger.info(
                "email_sent_success",
                to_email=to_email,
                subject=subject,
            )
            return True
        except Exception as e:
            import traceback as _tb
            logger.error(
                "email_send_failed",
                to_email=to_email,
                subject=subject,
                error=str(e),
                traceback=_tb.format_exc(),
            )
            raise

    @staticmethod
    def _html_to_text(html: str) -> str:
        """Converte HTML simples para texto puro."""
        import re

        # Remove tags HTML
        text = re.sub("<[^<]+?>", "", html)
        # Remove entidades HTML comuns
        text = text.replace("&nbsp;", " ")
        text = text.replace("&quot;", '"')
        text = text.replace("&apos;", "'")
        text = text.replace("&amp;", "&")
        return text


class EmailTemplateRenderer:
    """Renderizador de templates de email com Jinja2."""

    def __init__(self):
        """Inicializa ambiente Jinja2 para templates de notificações."""
        templates_dir = Path(__file__).resolve().parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_due_soon_email(
        self,
        user_name: str,
        book_title: str,
        due_date: datetime,
        days_left: int,
    ) -> str:
        """Renderiza email de aviso de vencimento próximo."""
        template = self.env.get_template("due_soon.html")
        return template.render(
            user_name=user_name,
            book_title=book_title,
            due_date=due_date.strftime("%d/%m/%Y"),
            days_left=days_left,
        )

    def render_overdue_email(
        self,
        user_name: str,
        book_title: str,
        due_date: datetime,
        days_overdue: int,
    ) -> str:
        """Renderiza email de empréstimo vencido."""
        template = self.env.get_template("overdue.html")
        return template.render(
            user_name=user_name,
            book_title=book_title,
            due_date=due_date.strftime("%d/%m/%Y"),
            days_overdue=days_overdue,
        )


class EmailNotificationService:
    """Serviço para envio de notificações por email."""

    def __init__(
        self,
        provider: EmailProvider,
        sender_name: str = "Biblioteca Virtual",
        sender_email: Optional[str] = None,
    ):
        self.provider = provider
        self.sender_name = sender_name
        self.sender_email = sender_email or "noreply@biblioteca-virtual.com"
        self.renderer = EmailTemplateRenderer()

    async def send_due_soon_notification(
        self,
        to_email: str,
        user_name: str,
        book_title: str,
        due_date: datetime,
        days_left: int,
    ) -> bool:
        """Envia notificação de vencimento próximo."""
        subject = f"⏰ Seu empréstimo vence em {days_left} dia(s)"
        html_content = self.renderer.render_due_soon_email(
            user_name=user_name,
            book_title=book_title,
            due_date=due_date,
            days_left=days_left,
        )
        return await self.provider.send_email(to_email, subject, html_content)

    async def send_overdue_notification(
        self,
        to_email: str,
        user_name: str,
        book_title: str,
        due_date: datetime,
        days_overdue: int,
    ) -> bool:
        """Envia notificação de empréstimo vencido."""
        subject = f"🚨 Empréstimo vencido há {days_overdue} dia(s)"
        html_content = self.renderer.render_overdue_email(
            user_name=user_name,
            book_title=book_title,
            due_date=due_date,
            days_overdue=days_overdue,
        )
        return await self.provider.send_email(to_email, subject, html_content)

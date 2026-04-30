import json
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Biblioteca Virtual API"
    app_version: str = "0.1.0"
    environment: str = "local"

    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    redis_enabled: bool = Field(True, alias="REDIS_ENABLED")

    secret_key: str = Field("change-me", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    cors_origins: str = Field("", alias="CORS_ORIGINS")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    rate_limit_enabled: bool = Field(True, alias="RATE_LIMIT_ENABLED")

    cache_ttl_seconds: int = Field(60, alias="CACHE_TTL_SECONDS")

    # Notificações
    notification_enabled: bool = Field(True, alias="NOTIFICATION_ENABLED")
    notification_scheduler_enabled: bool = Field(
        True, alias="NOTIFICATION_SCHEDULER_ENABLED"
    )
    notification_scheduler_interval_minutes: int = Field(
        60, alias="NOTIFICATION_SCHEDULER_INTERVAL_MINUTES"
    )
    notification_days_before: str = Field("3,1,0", alias="NOTIFICATION_DAYS_BEFORE")
    notification_enable_overdue_alerts: bool = Field(
        True, alias="NOTIFICATION_ENABLE_OVERDUE_ALERTS"
    )

    # Email
    email_provider: str = Field("mock", alias="EMAIL_PROVIDER")  # mock | smtp
    email_sender_name: str = Field("Biblioteca Virtual", alias="EMAIL_SENDER_NAME")
    email_sender_address: str = Field(
        "noreply@biblioteca-virtual.com", alias="EMAIL_SENDER_ADDRESS"
    )
    smtp_host: str = Field("localhost", alias="SMTP_HOST")
    smtp_port: int = Field(587, alias="SMTP_PORT")
    smtp_username: str = Field("", alias="SMTP_USERNAME")
    smtp_password: str = Field("", alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(True, alias="SMTP_USE_TLS")

    # Webhook
    webhook_enabled: bool = Field(False, alias="WEBHOOK_ENABLED")
    webhook_url: str = Field("", alias="WEBHOOK_URL")
    webhook_timeout: float = Field(10.0, alias="WEBHOOK_TIMEOUT")
    webhook_max_retries: int = Field(3, alias="WEBHOOK_MAX_RETRIES")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        value = self.cors_origins
        if not value:
            return []
        value = value.strip()
        if not value:
            return []
        if value.startswith("["):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def notification_days_before_list(self) -> list[int]:
        """Retorna lista de dias antes do vencimento para disparar notificações."""
        try:
            days = [int(d.strip()) for d in self.notification_days_before.split(",")]
            return sorted(set(days), reverse=True)  # Remove duplicatas e ordena
        except (ValueError, AttributeError):
            return [3, 1, 0]  # Default


@lru_cache
def get_settings() -> Settings:
    return Settings()

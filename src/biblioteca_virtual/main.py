from uuid import uuid4

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from biblioteca_virtual.api.v1.router import api_router
from biblioteca_virtual.core.cache import close_redis, init_redis
from biblioteca_virtual.core.config import get_settings
from biblioteca_virtual.core.errors import register_exception_handlers
from biblioteca_virtual.core.health import health_router
from biblioteca_virtual.core.logging import configure_logging
from biblioteca_virtual.core.metrics import setup_metrics
from biblioteca_virtual.core.middleware import auth_middleware
from biblioteca_virtual.core.rate_limit import init_rate_limiter
from biblioteca_virtual.core.scheduler import (
    init_notification_scheduler,
    shutdown_notification_scheduler,
)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    tags = [
        {"name": "Auth", "description": "Autenticacao e tokens"},
        {"name": "Users", "description": "Gestao de usuarios"},
        {"name": "Books", "description": "Catalogo de livros"},
        {"name": "Loans", "description": "Emprestimos e devolucoes"},
        {"name": "Health", "description": "Status da aplicacao"},
    ]

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        openapi_tags=tags,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    if settings.cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def request_context_middleware(request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        structlog.contextvars.clear_contextvars()
        return response

    app.include_router(api_router)
    app.include_router(health_router)

    register_exception_handlers(app)
    setup_metrics(app)
    auth_middleware(app)

    @app.on_event("startup")
    async def startup() -> None:
        # If tests override get_settings via app.dependency_overrides, skip external init
        if get_settings in app.dependency_overrides:
            await init_notification_scheduler(app)
            return

        current_settings = get_settings()
        if current_settings.redis_enabled:
            redis_client = await init_redis(current_settings.redis_url)
            if current_settings.rate_limit_enabled:
                await init_rate_limiter(redis_client)

        # Inicializa scheduler de notificações
        await init_notification_scheduler(app)

    @app.on_event("shutdown")
    async def shutdown() -> None:
        current_settings = get_settings()
        if current_settings.redis_enabled:
            await close_redis()

        # Encerra scheduler de notificações
        await shutdown_notification_scheduler()

    return app


app = create_app()

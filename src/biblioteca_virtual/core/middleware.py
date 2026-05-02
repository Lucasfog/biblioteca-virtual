import time
import structlog
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from biblioteca_virtual.core.config import get_settings
from biblioteca_virtual.core.db import get_engine_no_cache
from biblioteca_virtual.modules.users.repository import UserRepository

logger = structlog.get_logger(__name__)


PUBLIC_ROUTES = [
    ("GET", "/docs"),
    ("GET", "/openapi.json"),
    ("GET", "/redoc"),
    ("GET", "/health"),
    ("GET", "/metrics"),
    ("POST", "/api/v1/auth/token"),
    ("POST", "/api/v1/users"),
    ("POST", "/api/v1/users/"),
]

def is_public_route(method: str, path: str) -> bool:
    if method == "OPTIONS":
        return True
    if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
        return True
    return (method, path) in PUBLIC_ROUTES


class TokenPayload(BaseModel):
    sub: str
    exp: int


def auth_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def authentication_middleware(request: Request, call_next) -> Response:
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", str(uuid4()))

        structlog.contextvars.bind_contextvars(request_id=request_id)

        path = request.url.path
        is_public = is_public_route(request.method, path)

        if not is_public:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.warning("auth_missing_header", path=path)
                response = Response(
                    content='{"detail":"Unauthorized"}',
                    status_code=401,
                    media_type="application/json",
                )
                response.headers["X-Request-ID"] = request_id
                return response

            token = auth_header.replace("Bearer ", "")
            settings = get_settings()

            try:
                payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
                token_data = TokenPayload(**payload)
            except JWTError as exc:
                logger.warning("auth_token_invalid", path=path, error=str(exc))
                response = Response(
                    content='{"detail":"Unauthorized"}',
                    status_code=401,
                    media_type="application/json",
                )
                response.headers["X-Request-ID"] = request_id
                return response

            try:
                from uuid import UUID
                user_id = UUID(token_data.sub)
                engine = get_engine_no_cache()
                session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
                async with session_maker() as session:
                    user = await UserRepository(session).get_by_id(user_id)
                    if user is None:
                        logger.warning("auth_user_not_found", user_id=str(user_id))
                        response = Response(
                            content='{"detail":"Unauthorized"}',
                            status_code=401,
                            media_type="application/json",
                        )
                        response.headers["X-Request-ID"] = request_id
                        return response
                    request.state.user = user
            except Exception as exc:
                logger.warning("auth_validation_error", error=str(exc))
                response = Response(
                    content='{"detail":"Unauthorized"}',
                    status_code=401,
                    media_type="application/json",
                )
                response.headers["X-Request-ID"] = request_id
                return response

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        structlog.contextvars.clear_contextvars()
        return response

import structlog
from datetime import timedelta

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.core.config import get_settings, Settings
from biblioteca_virtual.core.db import get_session
from biblioteca_virtual.core.rate_limit import rate_limit_dependency
from biblioteca_virtual.core.security import create_access_token
from biblioteca_virtual.modules.auth.schemas import Token
from biblioteca_virtual.modules.auth.service import AuthService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth")


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(session)


@router.post(
    "/token",
    response_model=Token,
    summary="Gerar token de acesso",
    dependencies=[Depends(rate_limit_dependency(times=5, seconds=60))],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
):
    user = await service.authenticate_user(form_data.username, form_data.password)
    if user is None:
        logger.warning("login_failed", email=form_data.username, reason="invalid_credentials")
        from biblioteca_virtual.core.errors import UnauthorizedError
        raise UnauthorizedError("Credenciais invalidas")
    token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    logger.info("login_success", user_id=str(user.id), email=user.email)
    return Token(access_token=token, token_type="bearer")

from datetime import timedelta
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.core.config import get_settings
from biblioteca_virtual.core.db import get_session
from biblioteca_virtual.core.errors import UnauthorizedError
from biblioteca_virtual.shared.utils import utcnow
from biblioteca_virtual.modules.users.repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class TokenPayload(BaseModel):
    sub: str
    exp: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


async def get_current_user(
    request: Request,
    _token: str = Depends(oauth2_scheme)
):
    user = getattr(request.state, "user", None)
    if not user:
        raise UnauthorizedError("Usuario nao autenticado")
    return user

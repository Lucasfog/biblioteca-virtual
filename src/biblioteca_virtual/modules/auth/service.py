from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.core.errors import UnauthorizedError
from biblioteca_virtual.core.security import verify_password
from biblioteca_virtual.modules.users.repository import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)

    async def authenticate_user(self, email: str, password: str):
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Credenciais invalidas")
        if not user.is_active:
            raise UnauthorizedError("Usuario inativo")
        return user

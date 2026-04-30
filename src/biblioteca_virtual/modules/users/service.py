import structlog
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from biblioteca_virtual.core.errors import ConflictError, NotFoundError
from biblioteca_virtual.core.security import get_password_hash
from biblioteca_virtual.modules.loans.repository import LoanRepository
from biblioteca_virtual.modules.users.models import User
from biblioteca_virtual.modules.users.repository import UserRepository
from biblioteca_virtual.modules.users.schemas import UserCreate

logger = structlog.get_logger(__name__)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.loans = LoanRepository(session)

    async def list_users(self, offset: int, limit: int) -> tuple[list[User], int]:
        users, total = await self.users.list(offset, limit), await self.users.count()
        logger.info("users_service_list", offset=offset, limit=limit, total=total)
        return users, total

    async def create_user(self, payload: UserCreate) -> User:
        existing = await self.users.get_by_email(payload.email)
        if existing is not None:
            logger.warning("user_create_failed_email_exists", email=payload.email)
            raise ConflictError("Email ja cadastrado")

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
        )
        self.users.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        logger.info("user_service_created", user_id=str(user.id), email=user.email)
        return user

    async def get_user(self, user_id: UUID) -> User:
        user = await self.users.get_by_id(user_id)
        if user is None:
            logger.warning("user_not_found", user_id=str(user_id))
            raise NotFoundError("Usuario nao encontrado")
        logger.info("user_service_retrieved", user_id=str(user_id))
        return user

    async def list_user_loans(self, user_id: UUID, offset: int = 0, limit: int = 50) -> tuple[list, int]:
        user = await self.users.get_by_id(user_id)
        if user is None:
            logger.warning("user_not_found_for_loans", user_id=str(user_id))
            raise NotFoundError("Usuario nao encontrado")
        loans, total = await self.loans.list_by_user(user_id, offset, limit), await self.loans.count_by_user(user_id)
        logger.info("user_loans_service_listed", user_id=str(user_id), total=total)
        return loans, total

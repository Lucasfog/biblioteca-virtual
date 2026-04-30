from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from biblioteca_virtual.modules.loans.models import LoanStatus


class LoanCreate(BaseModel):
    user_id: UUID
    book_id: UUID


class LoanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    book_id: UUID
    status: LoanStatus
    due_at: datetime
    returned_at: datetime | None
    fine_cents: int | None
    created_at: datetime

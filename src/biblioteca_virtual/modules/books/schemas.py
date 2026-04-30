from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuthorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class BookCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    isbn: str = Field(min_length=10, max_length=32)
    author_name: str = Field(min_length=2, max_length=120)
    total_copies: int = Field(ge=1, le=1000)


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    isbn: str
    total_copies: int
    available_copies: int
    author: AuthorRead
    created_at: datetime


class BookAvailability(BaseModel):
    book_id: UUID
    available_copies: int
    is_available: bool

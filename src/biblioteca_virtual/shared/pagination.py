from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    offset: int = Field(0, ge=0, description="Posição inicial para paginação")
    limit: int = Field(50, ge=1, le=100, description="Quantidade de itens por página")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int

    @classmethod
    def build(cls, items: list[T], total: int, pagination: PaginationParams) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )

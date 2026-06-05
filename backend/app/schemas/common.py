"""
Common/Shared Pydantic Schemas
================================
Reused across multiple endpoints: pagination, health, base response, etc.
"""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base for all response schemas. Enables ORM mode."""
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseSchema, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int):
        import math
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if page_size else 1,
        )


class MessageResponse(BaseSchema):
    message: str
    detail: str | None = None


class HealthResponse(BaseSchema):
    status: str
    version: str
    environment: str
    timestamp: str

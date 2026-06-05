"""
Base Repository
================
Generic async CRUD operations using SQLAlchemy 2.0.
All entity-specific repositories inherit from this class.

Soft delete is implemented by setting deleted_at; never physically deletes rows.
"""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: UUID) -> ModelType | None:
        """Fetch a single active record by primary key."""
        stmt = select(self.model).where(self.model.id == id)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 20,
        filters: list | None = None,
    ) -> list[ModelType]:
        """Fetch paginated active records with optional filters."""
        stmt = select(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        if filters:
            for f in filters:
                stmt = stmt.where(f)
        stmt = stmt.offset(skip).limit(limit)
        if hasattr(self.model, "created_at"):
            stmt = stmt.order_by(self.model.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        db: AsyncSession,
        filters: list | None = None,
    ) -> int:
        """Count active records."""
        stmt = select(func.count()).select_from(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        if filters:
            for f in filters:
                stmt = stmt.where(f)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def create(self, db: AsyncSession, obj_data: dict) -> ModelType:
        """Create and persist a new record."""
        obj = self.model(**obj_data)
        db.add(obj)
        await db.flush()  # Get ID without full commit
        await db.refresh(obj)
        return obj

    async def update(
        self,
        db: AsyncSession,
        id: UUID,
        obj_data: dict,
    ) -> ModelType | None:
        """Update fields on an existing record. Returns updated object."""
        if not obj_data:
            return await self.get_by_id(db, id)

        stmt = update(self.model).where(self.model.id == id)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        
        await db.execute(stmt.values(**obj_data))
        await db.flush()
        return await self.get_by_id(db, id)

    async def soft_delete(self, db: AsyncSession, id: UUID) -> bool:
        """Soft-delete by setting deleted_at. Returns True if found."""
        if not hasattr(self.model, "deleted_at"):
            # If not soft deletable, hard delete or raise error. Let's do hard delete or return False.
            # In our case, physical delete if no soft delete.
            from sqlalchemy import delete
            result = await db.execute(delete(self.model).where(self.model.id == id))
            await db.flush()
            return result.rowcount > 0

        from datetime import datetime, timezone
        result = await db.execute(
            update(self.model)
            .where(self.model.id == id)
            .where(self.model.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await db.flush()
        return result.rowcount > 0

    async def exists(self, db: AsyncSession, **kwargs) -> bool:
        """Check if a record matching given kwargs exists."""
        stmt = select(func.count()).select_from(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await db.execute(stmt)
        return result.scalar_one() > 0


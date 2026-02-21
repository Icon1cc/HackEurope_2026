from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.invoice import Invoice
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, db: AsyncSession):
        super().__init__(Invoice, db)

    async def get_by_id(self, id: UUID) -> Invoice | None:
        result = await self.db.execute(
            select(Invoice).options(selectinload(Invoice.items)).where(Invoice.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Invoice]:
        result = await self.db.execute(
            select(Invoice).options(selectinload(Invoice.items)).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Invoice:
        instance = Invoice(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        # Re-fetch with eager loading
        return await self.get_by_id(instance.id)

    async def update(self, id: UUID, **kwargs) -> Invoice | None:
        instance = await self.get_by_id(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(instance, key, value)
        await self.db.commit()
        await self.db.refresh(instance)
        return await self.get_by_id(id)

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[Invoice]:
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(Invoice.status == status)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_flagged(self, skip: int = 0, limit: int = 100) -> list[Invoice]:
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(Invoice.status.in_(["flagged", "overcharge"]))
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

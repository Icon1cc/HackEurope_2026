from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.override import Override
from app.repositories.base import BaseRepository


class OverrideRepository(BaseRepository[Override]):
    def __init__(self, db: AsyncSession):
        super().__init__(Override, db)

    async def get_by_invoice_id(self, invoice_id: UUID) -> list[Override]:
        result = await self.db.execute(
            select(Override).where(Override.invoice_id == invoice_id)
        )
        return list(result.scalars().all())

    async def get_by_vendor_id(self, vendor_id: UUID) -> list[Override]:
        result = await self.db.execute(
            select(Override).where(Override.vendor_id == vendor_id)
        )
        return list(result.scalars().all())

    async def get_disagreements(self, skip: int = 0, limit: int = 100) -> list[Override]:
        result = await self.db.execute(
            select(Override).where(Override.agreed == False).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

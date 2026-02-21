from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.invoice import Invoice
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, db: AsyncSession):
        super().__init__(Invoice, db)

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[Invoice]:
        result = await self.db.execute(
            select(Invoice).where(Invoice.status == status).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_flagged(self, skip: int = 0, limit: int = 100) -> list[Invoice]:
        result = await self.db.execute(
            select(Invoice).where(Invoice.status.in_(["flagged", "overcharge"])).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

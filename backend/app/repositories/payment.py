from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Payment, db)

    async def get_by_invoice_id(self, invoice_id: UUID) -> list[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.invoice_id == invoice_id)
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.status == status).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

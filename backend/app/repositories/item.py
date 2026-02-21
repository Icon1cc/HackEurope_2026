from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.item import Item
from app.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    def __init__(self, db: AsyncSession):
        super().__init__(Item, db)

    async def get_by_invoice_id(self, invoice_id: UUID, skip: int = 0, limit: int = 100) -> list[Item]:
        result = await self.db.execute(
            select(Item).where(Item.invoice_id == invoice_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

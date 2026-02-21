from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.market_data import MarketData
from app.repositories.base import BaseRepository


class MarketDataRepository(BaseRepository[MarketData]):
    def __init__(self, db: AsyncSession):
        super().__init__(MarketData, db)

    async def get_by_category(self, category: str, skip: int = 0, limit: int = 100) -> list[MarketData]:
        result = await self.db.execute(
            select(MarketData).where(MarketData.category == category).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> list[MarketData]:
        result = await self.db.execute(
            select(MarketData).where(MarketData.name == name)
        )
        return list(result.scalars().all())

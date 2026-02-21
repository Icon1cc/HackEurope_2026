from uuid import UUID
from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import MarketDataCreate, MarketDataUpdate, MarketDataResponse


class MarketDataService:
    def __init__(self, repo: MarketDataRepository):
        self.repo = repo

    async def get_market_data(self, id: UUID) -> MarketDataResponse | None:
        data = await self.repo.get_by_id(id)
        return MarketDataResponse.model_validate(data) if data else None

    async def get_all_market_data(self, skip: int = 0, limit: int = 100) -> list[MarketDataResponse]:
        data = await self.repo.get_all(skip, limit)
        return [MarketDataResponse.model_validate(d) for d in data]

    async def get_by_category(self, category: str, skip: int = 0, limit: int = 100) -> list[MarketDataResponse]:
        data = await self.repo.get_by_category(category, skip, limit)
        return [MarketDataResponse.model_validate(d) for d in data]

    async def get_by_name(self, name: str) -> list[MarketDataResponse]:
        data = await self.repo.get_by_name(name)
        return [MarketDataResponse.model_validate(d) for d in data]

    async def create_market_data(self, data: MarketDataCreate) -> MarketDataResponse:
        entry = await self.repo.create(**data.model_dump(exclude_unset=True))
        return MarketDataResponse.model_validate(entry)

    async def update_market_data(self, id: UUID, data: MarketDataUpdate) -> MarketDataResponse | None:
        entry = await self.repo.update(id, **data.model_dump(exclude_unset=True))
        return MarketDataResponse.model_validate(entry) if entry else None

    async def delete_market_data(self, id: UUID) -> bool:
        return await self.repo.delete(id)

from uuid import UUID
from app.repositories.item import ItemRepository
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse


class ItemService:
    def __init__(self, repo: ItemRepository):
        self.repo = repo

    async def get_item(self, id: UUID) -> ItemResponse | None:
        item = await self.repo.get_by_id(id)
        return ItemResponse.model_validate(item) if item else None

    async def get_all_items(self, skip: int = 0, limit: int = 100) -> list[ItemResponse]:
        items = await self.repo.get_all(skip, limit)
        return [ItemResponse.model_validate(i) for i in items]

    async def get_by_invoice_id(self, invoice_id: UUID, skip: int = 0, limit: int = 100) -> list[ItemResponse]:
        items = await self.repo.get_by_invoice_id(invoice_id, skip, limit)
        return [ItemResponse.model_validate(i) for i in items]

    async def create_item(self, data: ItemCreate) -> ItemResponse:
        item = await self.repo.create(**data.model_dump(exclude_unset=True))
        return ItemResponse.model_validate(item)

    async def update_item(self, id: UUID, data: ItemUpdate) -> ItemResponse | None:
        item = await self.repo.update(id, **data.model_dump(exclude_unset=True))
        return ItemResponse.model_validate(item) if item else None

    async def delete_item(self, id: UUID) -> bool:
        return await self.repo.delete(id)

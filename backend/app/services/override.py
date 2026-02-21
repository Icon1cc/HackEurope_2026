from uuid import UUID
from app.repositories.override import OverrideRepository
from app.schemas.override import OverrideCreate, OverrideUpdate, OverrideResponse


class OverrideService:
    def __init__(self, repo: OverrideRepository):
        self.repo = repo

    async def get_override(self, id: UUID) -> OverrideResponse | None:
        override = await self.repo.get_by_id(id)
        return OverrideResponse.model_validate(override) if override else None

    async def get_all_overrides(self, skip: int = 0, limit: int = 100) -> list[OverrideResponse]:
        overrides = await self.repo.get_all(skip, limit)
        return [OverrideResponse.model_validate(o) for o in overrides]

    async def get_by_invoice_id(self, invoice_id: UUID) -> list[OverrideResponse]:
        overrides = await self.repo.get_by_invoice_id(invoice_id)
        return [OverrideResponse.model_validate(o) for o in overrides]

    async def get_by_vendor_id(self, vendor_id: UUID) -> list[OverrideResponse]:
        overrides = await self.repo.get_by_vendor_id(vendor_id)
        return [OverrideResponse.model_validate(o) for o in overrides]

    async def get_disagreements(self, skip: int = 0, limit: int = 100) -> list[OverrideResponse]:
        overrides = await self.repo.get_disagreements(skip, limit)
        return [OverrideResponse.model_validate(o) for o in overrides]

    async def create_override(self, data: OverrideCreate) -> OverrideResponse:
        override = await self.repo.create(**data.model_dump(exclude_unset=True))
        return OverrideResponse.model_validate(override)

    async def update_override(self, id: UUID, data: OverrideUpdate) -> OverrideResponse | None:
        override = await self.repo.update(id, **data.model_dump(exclude_unset=True))
        return OverrideResponse.model_validate(override) if override else None

    async def delete_override(self, id: UUID) -> bool:
        return await self.repo.delete(id)

from uuid import UUID
from app.repositories.vendor import VendorRepository
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorResponse, VendorSummary


class VendorService:
    def __init__(self, repo: VendorRepository):
        self.repo = repo

    async def get_vendor(self, id: UUID) -> VendorResponse | None:
        vendor = await self.repo.get_by_id(id)
        return VendorResponse.model_validate(vendor) if vendor else None

    async def get_all_vendors(self, skip: int = 0, limit: int = 100) -> list[VendorResponse]:
        vendors = await self.repo.get_all(skip, limit)
        return [VendorResponse.model_validate(v) for v in vendors]

    async def get_by_name(self, name: str) -> VendorResponse | None:
        vendor = await self.repo.get_by_name(name)
        return VendorResponse.model_validate(vendor) if vendor else None

    async def get_by_email(self, email: str) -> VendorResponse | None:
        vendor = await self.repo.get_by_email(email)
        return VendorResponse.model_validate(vendor) if vendor else None

    async def create_vendor(self, data: VendorCreate) -> VendorResponse:
        vendor = await self.repo.create(**data.model_dump(exclude_unset=True))
        return VendorResponse.model_validate(vendor)

    async def update_vendor(self, id: UUID, data: VendorUpdate) -> VendorResponse | None:
        vendor = await self.repo.update(id, **data.model_dump(exclude_unset=True))
        return VendorResponse.model_validate(vendor) if vendor else None

    async def get_vendor_summary(self, vendor_id: UUID) -> VendorSummary | None:
        data = await self.repo.get_vendor_summary(vendor_id)
        return VendorSummary(**data) if data else None

    async def delete_vendor(self, id: UUID) -> bool:
        return await self.repo.delete(id)

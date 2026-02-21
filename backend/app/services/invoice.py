from uuid import UUID
from app.repositories.invoice import InvoiceRepository
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse


class InvoiceService:
    def __init__(self, repo: InvoiceRepository):
        self.repo = repo

    async def get_invoice(self, id: UUID) -> InvoiceResponse | None:
        invoice = await self.repo.get_by_id(id)
        return InvoiceResponse.model_validate(invoice) if invoice else None

    async def get_all_invoices(self, skip: int = 0, limit: int = 100) -> list[InvoiceResponse]:
        invoices = await self.repo.get_all(skip, limit)
        return [InvoiceResponse.model_validate(i) for i in invoices]

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[InvoiceResponse]:
        invoices = await self.repo.get_by_status(status, skip, limit)
        return [InvoiceResponse.model_validate(i) for i in invoices]

    async def get_flagged(self, skip: int = 0, limit: int = 100) -> list[InvoiceResponse]:
        invoices = await self.repo.get_flagged(skip, limit)
        return [InvoiceResponse.model_validate(i) for i in invoices]

    async def create_invoice(self, data: InvoiceCreate) -> InvoiceResponse:
        invoice = await self.repo.create(**data.model_dump(exclude_unset=True))
        return InvoiceResponse.model_validate(invoice)

    async def update_invoice(self, id: UUID, data: InvoiceUpdate) -> InvoiceResponse | None:
        invoice = await self.repo.update(id, **data.model_dump(exclude_unset=True))
        return InvoiceResponse.model_validate(invoice) if invoice else None

    async def delete_invoice(self, id: UUID) -> bool:
        return await self.repo.delete(id)

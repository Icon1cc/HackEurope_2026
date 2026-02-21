from uuid import UUID
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse


class PaymentService:
    def __init__(self, repo: PaymentRepository):
        self.repo = repo

    async def get_payment(self, id: UUID) -> PaymentResponse | None:
        payment = await self.repo.get_by_id(id)
        return PaymentResponse.model_validate(payment) if payment else None

    async def get_all_payments(self, skip: int = 0, limit: int = 100) -> list[PaymentResponse]:
        payments = await self.repo.get_all(skip, limit)
        return [PaymentResponse.model_validate(p) for p in payments]

    async def get_by_invoice_id(self, invoice_id: UUID) -> list[PaymentResponse]:
        payments = await self.repo.get_by_invoice_id(invoice_id)
        return [PaymentResponse.model_validate(p) for p in payments]

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[PaymentResponse]:
        payments = await self.repo.get_by_status(status, skip, limit)
        return [PaymentResponse.model_validate(p) for p in payments]

    async def create_payment(self, data: PaymentCreate) -> PaymentResponse:
        payment = await self.repo.create(**data.model_dump(exclude_unset=True))
        return PaymentResponse.model_validate(payment)

    async def update_payment(self, id: UUID, data: PaymentUpdate) -> PaymentResponse | None:
        payment = await self.repo.update(id, **data.model_dump(exclude_unset=True))
        return PaymentResponse.model_validate(payment) if payment else None

    async def delete_payment(self, id: UUID) -> bool:
        return await self.repo.delete(id)

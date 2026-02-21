from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class PaymentCreate(BaseModel):
    invoice_id: UUID
    amount: Decimal
    currency: str = "EUR"
    stripe_payout_id: str | None = None


class PaymentUpdate(BaseModel):
    stripe_payout_id: str | None = None
    status: str | None = None
    confirmed_at: datetime | None = None


class PaymentResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    stripe_payout_id: str | None
    amount: Decimal
    currency: str
    status: str
    initiated_at: datetime
    confirmed_at: datetime | None

    model_config = {"from_attributes": True}

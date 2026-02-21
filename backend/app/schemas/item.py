from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class ItemCreate(BaseModel):
    invoice_id: UUID
    description: str
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    total_price: Decimal | None = None
    unit: str | None = None


class ItemUpdate(BaseModel):
    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    total_price: Decimal | None = None
    unit: str | None = None


class ItemResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    description: str
    quantity: Decimal | None
    unit_price: Decimal | None
    total_price: Decimal | None
    unit: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field


class VendorCreate(BaseModel):
    name: str
    category: str = "computing"
    email: str | None = None
    registered_iban: str | None = None
    vendor_address: str | None = None


class VendorUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    email: str | None = None
    registered_iban: str | None = None
    vendor_address: str | None = None
    known_iban_changes: list[dict[str, Any]] | None = None
    avg_invoice_amount: Decimal | None = None
    invoice_count: int | None = None
    trust_score: Decimal | None = Field(None, ge=0, le=1)
    auto_approve_threshold: int | None = Field(None, ge=0, le=100)


class VendorSummary(BaseModel):
    vendor_id: UUID
    vendor_name: str
    category: str | None
    invoices_processed: int
    invoices_processing: int
    invoices_rejected: int
    total_amount_accepted: Decimal
    trust_score: Decimal


class VendorResponse(BaseModel):
    id: UUID
    name: str
    category: str | None
    email: str | None
    registered_iban: str | None
    known_iban_changes: list[dict[str, Any]] | None
    avg_invoice_amount: Decimal | None
    invoice_count: int
    trust_score: Decimal
    auto_approve_threshold: int
    vendor_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

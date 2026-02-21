from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field

from app.schemas.item import ItemResponse


class InvoiceCreate(BaseModel):
    raw_file_url: str | None = None
    vendor_id: UUID | None = None
    client_id: UUID | None = None


class InvoiceUpdate(BaseModel):
    extracted_data: dict[str, Any] | None = None
    anomalies: list[dict[str, Any]] | None = None
    market_benchmarks: dict[str, Any] | None = None
    confidence_score: int | None = Field(None, ge=0, le=100)
    status: str | None = None
    claude_summary: str | None = None
    negotiation_email: str | None = None
    auto_approved: bool | None = None


class InvoiceResponse(BaseModel):
    id: UUID
    vendor_id: UUID | None
    client_id: UUID | None
    invoice_number: str | None = None
    due_date: datetime | None = None
    vendor_name: str | None = None
    vendor_address: str | None = None
    client_name: str | None = None
    client_address: str | None = None
    subtotal: Decimal | None = None
    tax: Decimal | None = None
    total: Decimal | None = None
    currency: str | None = None
    raw_file_url: str | None
    extracted_data: dict[str, Any] | None
    anomalies: list[dict[str, Any]] | None
    market_benchmarks: dict[str, Any] | None
    confidence_score: int | None
    status: str
    claude_summary: str | None
    negotiation_email: str | None
    auto_approved: bool
    items: list[ItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


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
    raw_file_url: str | None
    extracted_data: dict[str, Any] | None
    anomalies: list[dict[str, Any]] | None
    market_benchmarks: dict[str, Any] | None
    confidence_score: int | None
    status: str
    claude_summary: str | None
    negotiation_email: str | None
    auto_approved: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

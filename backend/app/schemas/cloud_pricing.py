from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class CloudPricingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor: str
    service_name: str
    category: str
    sku_id: str
    description: Optional[str]
    region: Optional[str]
    instance_type: Optional[str]
    operating_system: Optional[str]
    price_per_unit: Decimal
    unit: str
    price_per_hour: Optional[Decimal]
    currency: str
    effective_date: Optional[datetime]
    source_api: str
    created_at: datetime
    updated_at: datetime


class InvoiceLineItem(BaseModel):
    """A single line from the customer invoice to validate."""
    vendor: str
    sku_id: Optional[str] = None
    instance_type: Optional[str] = None
    region: Optional[str] = None
    hours: Decimal
    billed_amount: Decimal


class InvoiceCheckRequest(BaseModel):
    items: List[InvoiceLineItem]


class LineItemResult(BaseModel):
    line: InvoiceLineItem
    matched_sku: Optional[CloudPricingResponse]
    expected_amount: Optional[Decimal]
    billed_amount: Decimal
    discrepancy: Optional[Decimal]
    discrepancy_pct: Optional[Decimal]
    status: str  # OK | OVERBILLED | UNDERBILLED | NO_MATCH


class InvoiceCheckResponse(BaseModel):
    total_billed: Decimal
    total_expected: Decimal
    total_discrepancy: Decimal
    items: List[LineItemResult]


class SyncStatus(BaseModel):
    last_sync: Optional[datetime]
    total_skus: int
    by_vendor: Dict[str, int]
    by_category: Dict[str, int]
    message: str

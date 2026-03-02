"""
pricing/schemas.py
Pydantic v2 schemas used by FastAPI request/response validation.
"""

from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


# ── Base read schema ───────────────────────────────────────────────────────
class CloudPricingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:               int
    vendor:           str
    service_name:     str
    category:         str
    sku_id:           str
    description:      Optional[str]
    region:           Optional[str]
    instance_type:    Optional[str]
    operating_system: Optional[str]

    price_per_unit:   Decimal
    unit:             str
    price_per_hour:   Optional[Decimal]   # NULL for non-hourly SKUs
    currency:         str
    effective_date:   Optional[datetime]

    source_api:       str
    updated_at:       datetime


# ── Filters for the /pricing endpoint ─────────────────────────────────────
class PricingFilter(BaseModel):
    vendor:        Optional[str]  = None   # aws | azure | gcp
    category:      Optional[str]  = None   # Compute | Storage | …
    region:        Optional[str]  = None
    instance_type: Optional[str]  = None
    service_name:  Optional[str]  = None
    page:          int            = 1
    page_size:     int            = 50


# ── Invoice check ──────────────────────────────────────────────────────────
class InvoiceLineItem(BaseModel):
    """A single line from the customer invoice to validate."""
    vendor:        str               # aws | azure | gcp
    sku_id:        Optional[str]  = None
    instance_type: Optional[str]  = None
    region:        Optional[str]  = None
    hours:         Decimal           # usage hours billed
    billed_amount: Decimal           # what the invoice charges (USD)


class InvoiceCheckRequest(BaseModel):
    items: List[InvoiceLineItem]


class LineItemResult(BaseModel):
    line:              InvoiceLineItem
    matched_sku:       Optional[CloudPricingRead]
    expected_amount:   Optional[Decimal]        # price_per_hour * hours
    billed_amount:     Decimal
    discrepancy:       Optional[Decimal]        # billed - expected  (+ = overbilled)
    discrepancy_pct:   Optional[Decimal]        # % vs expected
    status:            str                      # OK | OVERBILLED | UNDERBILLED | NO_MATCH


class InvoiceCheckResponse(BaseModel):
    total_billed:      Decimal
    total_expected:    Decimal
    total_discrepancy: Decimal
    items:             List[LineItemResult]


# ── Sync status ────────────────────────────────────────────────────────────
class SyncStatus(BaseModel):
    last_sync:   Optional[datetime]
    total_skus:  int
    by_vendor:   Dict[str, int]
    by_category: Dict[str, int]
    message:     str

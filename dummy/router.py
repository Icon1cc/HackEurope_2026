"""
router.py
FastAPI router — all /pricing endpoints.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from pricing import fetcher, normalizer, service
from pricing.schemas import (
    CloudPricingRead,
    InvoiceCheckRequest,
    InvoiceCheckResponse,
    SyncStatus,
)

logger  = logging.getLogger(__name__)
router  = APIRouter(prefix="/pricing", tags=["pricing"])


# ─────────────────────────────────────────────────────────────────────────────
# Sync
# ─────────────────────────────────────────────────────────────────────────────

def _run_full_sync(db: Session) -> None:
    """Fetch → normalise → upsert. Called by both the manual trigger and the worker."""
    logger.info("Starting full pricing sync …")
    payloads = fetcher.fetch_all()
    records  = normalizer.normalize_all(payloads)
    logger.info("Normalised %d records across all sources", len(records))
    affected, _ = service.upsert_pricing_records(db, records)
    logger.info("Sync complete — %d rows upserted", affected)


@router.post(
    "/sync",
    summary="Manually trigger a full pricing data refresh",
    response_model=SyncStatus,
)
def trigger_sync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Enqueue a full fetch+normalise+upsert cycle in the background.
    Returns current sync status immediately; the update runs asynchronously.
    """
    background_tasks.add_task(_run_full_sync, db)
    status = service.get_sync_status(db)
    status.message = "Sync triggered — running in background"
    return status


@router.get(
    "/sync/status",
    summary="Current state of the pricing database",
    response_model=SyncStatus,
)
def sync_status(db: Session = Depends(get_db)):
    return service.get_sync_status(db)


# ─────────────────────────────────────────────────────────────────────────────
# Browse / query
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    summary="List and filter pricing SKUs",
    response_model=List[CloudPricingRead],
)
def list_pricing(
    vendor:        Optional[str] = Query(None, description="aws | azure | gcp"),
    category:      Optional[str] = Query(None, description="Compute | Storage | Database | CDN"),
    region:        Optional[str] = Query(None, description="Partial match, e.g. eu-west"),
    instance_type: Optional[str] = Query(None, description="e.g. m6i.4xlarge"),
    service_name:  Optional[str] = Query(None, description="Partial match on service name"),
    page:          int           = Query(1,    ge=1),
    page_size:     int           = Query(50,   ge=1, le=500),
    db:            Session       = Depends(get_db),
):
    items, _ = service.get_pricing(
        db,
        vendor=vendor,
        category=category,
        region=region,
        instance_type=instance_type,
        service_name=service_name,
        page=page,
        page_size=page_size,
    )
    return items


@router.get(
    "/{pricing_id}",
    summary="Get a single pricing SKU by internal ID",
    response_model=CloudPricingRead,
)
def get_pricing_by_id(pricing_id: int, db: Session = Depends(get_db)):
    from pricing.models import CloudPricing
    item = db.query(CloudPricing).get(pricing_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Pricing record {pricing_id} not found")
    return item


# ─────────────────────────────────────────────────────────────────────────────
# Invoice checker
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/invoice/check",
    summary="Validate invoice line items against stored pricing",
    response_model=InvoiceCheckResponse,
)
def check_invoice(
    req: InvoiceCheckRequest,
    db:  Session = Depends(get_db),
):
    """
    Submit a list of invoice line items (vendor + instance_type + hours + billed_amount).
    Returns per-line match results with expected vs billed amounts and discrepancy flags.
    """
    return service.check_invoice(db, req)

"""
pricing/service.py

Database service layer — upsert logic and invoice checking.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from pricing.models import CloudPricing
from pricing.schemas import (
    InvoiceCheckRequest,
    InvoiceCheckResponse,
    InvoiceLineItem,
    LineItemResult,
    SyncStatus,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Upsert
# ─────────────────────────────────────────────────────────────────────────────

def upsert_pricing_records(db: Session, records: List[dict]) -> Tuple[int, int]:
    """
    Upsert a list of normalised pricing dicts into cloud_pricing.

    Conflict resolution: on (vendor, sku_id, source_api) update all mutable
    fields and bump updated_at.

    Returns (inserted_count, updated_count) — approximated via row_count.
    """
    if not records:
        return 0, 0

    # SQLAlchemy core insert with ON CONFLICT
    table = CloudPricing.__table__

    # Chunk to avoid enormous single statements
    CHUNK = 500
    total_affected = 0

    for i in range(0, len(records), CHUNK):
        chunk = records[i : i + CHUNK]

        stmt = pg_insert(table).values(chunk)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_pricing_vendor_sku_source",
            set_={
                "service_name":     stmt.excluded.service_name,
                "category":         stmt.excluded.category,
                "description":      stmt.excluded.description,
                "region":           stmt.excluded.region,
                "instance_type":    stmt.excluded.instance_type,
                "operating_system": stmt.excluded.operating_system,
                "price_per_unit":   stmt.excluded.price_per_unit,
                "unit":             stmt.excluded.unit,
                "price_per_hour":   stmt.excluded.price_per_hour,
                "currency":         stmt.excluded.currency,
                "effective_date":   stmt.excluded.effective_date,
                "raw_attributes":   stmt.excluded.raw_attributes,
                "updated_at":       func.now(),
            },
        )

        result = db.execute(stmt)
        total_affected += result.rowcount
        db.commit()
        logger.debug("Upserted chunk %d–%d (%d rows)", i, i + len(chunk), result.rowcount)

    logger.info("Total rows affected: %d (of %d submitted)", total_affected, len(records))
    return total_affected, 0   # PG rowcount for upserts counts both inserts+updates


# ─────────────────────────────────────────────────────────────────────────────
# Query helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_pricing(
    db: Session,
    vendor:        Optional[str] = None,
    category:      Optional[str] = None,
    region:        Optional[str] = None,
    instance_type: Optional[str] = None,
    service_name:  Optional[str] = None,
    page:          int = 1,
    page_size:     int = 50,
) -> Tuple[List[CloudPricing], int]:
    """Return a paginated, filtered list of CloudPricing rows + total count."""
    q = db.query(CloudPricing)

    if vendor:
        q = q.filter(CloudPricing.vendor == vendor.lower())
    if category:
        q = q.filter(CloudPricing.category == category)
    if region:
        q = q.filter(CloudPricing.region.ilike(f"%{region}%"))
    if instance_type:
        q = q.filter(CloudPricing.instance_type.ilike(f"%{instance_type}%"))
    if service_name:
        q = q.filter(CloudPricing.service_name.ilike(f"%{service_name}%"))

    total = q.count()
    items = q.order_by(CloudPricing.vendor, CloudPricing.service_name) \
             .offset((page - 1) * page_size) \
             .limit(page_size) \
             .all()
    return items, total


def get_sync_status(db: Session) -> SyncStatus:
    """Return aggregate stats about the current pricing data."""
    total = db.query(func.count(CloudPricing.id)).scalar() or 0

    by_vendor = {
        row.vendor: row.cnt
        for row in db.query(
            CloudPricing.vendor,
            func.count(CloudPricing.id).label("cnt")
        ).group_by(CloudPricing.vendor).all()
    }

    by_category = {
        row.category: row.cnt
        for row in db.query(
            CloudPricing.category,
            func.count(CloudPricing.id).label("cnt")
        ).group_by(CloudPricing.category).all()
    }

    last_sync = db.query(func.max(CloudPricing.updated_at)).scalar()

    return SyncStatus(
        last_sync=last_sync,
        total_skus=total,
        by_vendor=by_vendor,
        by_category=by_category,
        message="OK" if total > 0 else "No data yet — trigger a sync via POST /pricing/sync",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Invoice checker
# ─────────────────────────────────────────────────────────────────────────────

def _find_best_match(
    db: Session,
    item: InvoiceLineItem,
) -> Optional[CloudPricing]:
    """
    Try to find the best-matching SKU for an invoice line item.

    Match priority:
      1. Exact sku_id + vendor
      2. instance_type + vendor + region (closest region match)
      3. instance_type + vendor (any region)
    Only considers hourly SKUs (price_per_hour IS NOT NULL).
    """
    vendor = item.vendor.lower()
    q = db.query(CloudPricing).filter(
        CloudPricing.vendor == vendor,
        CloudPricing.price_per_hour.isnot(None),
    )

    # 1 – exact SKU
    if item.sku_id:
        match = q.filter(CloudPricing.sku_id == item.sku_id).first()
        if match:
            return match

    # 2 – instance_type + region
    if item.instance_type and item.region:
        match = q.filter(
            CloudPricing.instance_type.ilike(item.instance_type),
            CloudPricing.region.ilike(f"%{item.region}%"),
        ).first()
        if match:
            return match

    # 3 – instance_type only
    if item.instance_type:
        match = q.filter(
            CloudPricing.instance_type.ilike(item.instance_type),
        ).first()
        if match:
            return match

    return None


def check_invoice(db: Session, req: InvoiceCheckRequest) -> InvoiceCheckResponse:
    """
    Compare each invoice line item against the stored pricing catalogue.

    Returns per-line match details + totals.
    """
    line_results: List[LineItemResult] = []
    total_billed   = Decimal("0")
    total_expected = Decimal("0")

    for item in req.items:
        total_billed += item.billed_amount
        match = _find_best_match(db, item)

        if match is None:
            line_results.append(LineItemResult(
                line=item,
                matched_sku=None,
                expected_amount=None,
                billed_amount=item.billed_amount,
                discrepancy=None,
                discrepancy_pct=None,
                status="NO_MATCH",
            ))
            continue

        expected = match.price_per_hour * item.hours
        total_expected += expected
        discrepancy    = item.billed_amount - expected
        pct            = (discrepancy / expected * 100).quantize(Decimal("0.01")) if expected else None

        if abs(discrepancy) < Decimal("0.01"):
            status = "OK"
        elif discrepancy > 0:
            status = "OVERBILLED"
        else:
            status = "UNDERBILLED"

        # Import here to avoid circular — the schema needs the ORM model
        from pricing.schemas import CloudPricingRead
        line_results.append(LineItemResult(
            line=item,
            matched_sku=CloudPricingRead.model_validate(match),
            expected_amount=expected.quantize(Decimal("0.0001")),
            billed_amount=item.billed_amount,
            discrepancy=discrepancy.quantize(Decimal("0.0001")),
            discrepancy_pct=pct,
            status=status,
        ))

    return InvoiceCheckResponse(
        total_billed=total_billed,
        total_expected=total_expected,
        total_discrepancy=(total_billed - total_expected).quantize(Decimal("0.0001")),
        items=line_results,
    )

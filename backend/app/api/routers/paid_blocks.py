"""Proxy for @paid-ai/paid-blocks frontend components.

Fetches data from Paid.ai via the paid-python SDK and falls back to
the local database when the Paid.ai API has no data (e.g. orders /
billing not yet configured).

Route patterns expected by the components (without baseUrl):
  GET /api/usage/{customerExternalId}
  GET /api/invoices/{customerExternalId}

This router is mounted at /api/paid-blocks and the Vite dev proxy
rewrites the component requests to hit these endpoints.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.invoice import Invoice
from app.services.paid_service import get_paid_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/paid-blocks", tags=["paid-blocks"])

MANUAL_REVIEW_MINUTES = 12.0   # assumed manual review time per invoice
HOURLY_RATE_EUR = 50.0         # cost of manual reviewer per hour
PER_INVOICE_SAVINGS_CENTS = int(MANUAL_REVIEW_MINUTES / 60.0 * HOURLY_RATE_EUR * 100)


def _to_cents(value: Decimal | float | None) -> int:
    """Convert EUR amount to integer cents."""
    if value is None:
        return 0
    return int(round(float(value) * 100))


# ── Paid.ai helpers ────────────────────────────────────────────

async def _get_paid_customer_id(external_id: str) -> str | None:
    """Resolve a vendor UUID (our external_customer_id) to a Paid.ai display ID."""
    client = get_paid_client()
    if client is None:
        return None
    try:
        customer = await client.customers.get_customer_by_external_id(external_id)
        return customer.id
    except Exception:
        return None


async def _fetch_paid_invoices(customer_external_id: str) -> list[dict] | None:
    """Try to fetch invoices from Paid.ai for a customer.

    Returns a list of dicts in PaidInvoiceTable format, or None if
    the SDK is unavailable or Paid.ai has no invoices.
    """
    client = get_paid_client()
    if client is None:
        return None

    paid_customer_id = await _get_paid_customer_id(customer_external_id)
    if not paid_customer_id:
        return None

    try:
        response = await client.invoices.list_invoices(limit=100)
        customer_invoices = [
            inv for inv in response.data
            if inv.customer_id == paid_customer_id
        ]
        if not customer_invoices:
            return None

        result = []
        for idx, inv in enumerate(customer_invoices, start=1):
            result.append({
                "id": inv.id,
                "number": idx,
                "paymentStatus": inv.payment_status,
                "issueDate": inv.issue_date.isoformat() if inv.issue_date else None,
                "dueDate": inv.due_date.isoformat() if inv.due_date else None,
                "invoiceTotal": int(round(inv.invoice_total)),
                "currency": inv.currency or "EUR",
            })
        return result
    except Exception as exc:
        logger.warning("Paid.ai invoices fetch failed: %s", exc)
        return None


# ── Endpoints ──────────────────────────────────────────────────

@router.get("/usage/{customer_external_id}")
async def proxy_usage(
    customer_external_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Build usageSummary from local invoice data for a vendor."""

    # Validate UUID
    try:
        vendor_uuid = uuid.UUID(customer_external_id)
    except ValueError:
        return _empty_response(customer_external_id)

    # ── Aggregate invoice stats for this vendor ──────────────
    row = (
        await db.execute(
            select(
                func.count(Invoice.id).label("total_count"),
                func.coalesce(func.sum(Invoice.total), 0).label("total_sum"),
                func.min(Invoice.created_at).label("first_date"),
                func.max(Invoice.created_at).label("last_date"),
                # Rejected / flagged invoices (fraud blocked)
                func.sum(
                    case(
                        (Invoice.status.in_(["rejected", "overcharge"]), Invoice.total),
                        else_=Decimal(0),
                    )
                ).label("fraud_total"),
                func.sum(
                    case(
                        (Invoice.status.in_(["rejected", "overcharge"]), 1),
                        else_=0,
                    )
                ).label("fraud_count"),
                # Negotiation emails sent
                func.sum(
                    case(
                        (Invoice.negotiation_email.isnot(None), 1),
                        else_=0,
                    )
                ).label("negotiation_count"),
                # Low-confidence flagged invoices
                func.sum(
                    case(
                        (Invoice.confidence_score < 40, 1),
                        else_=0,
                    )
                ).label("flagged_count"),
            ).where(Invoice.vendor_id == vendor_uuid)
        )
    ).one_or_none()

    if row is None or row.total_count == 0:
        return _empty_response(customer_external_id)

    now = datetime.now(timezone.utc)
    start = row.first_date or now
    end = row.last_date or now

    summaries: list[dict] = []

    # 1. Time Saved
    if row.total_count > 0:
        summaries.append({
            "id": f"ts-{customer_external_id[:8]}",
            "customerId": customer_external_id,
            "eventName": "time_saved_minutes",
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "eventsQuantity": row.total_count,
            "subtotal": row.total_count * PER_INVOICE_SAVINGS_CENTS,
            "currency": "EUR",
        })

    # 2. Fraud Blocked
    if row.fraud_count and row.fraud_count > 0:
        summaries.append({
            "id": f"fb-{customer_external_id[:8]}",
            "customerId": customer_external_id,
            "eventName": "fraud_blocked_euros",
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "eventsQuantity": int(row.fraud_count),
            "subtotal": _to_cents(row.fraud_total),
            "currency": "EUR",
        })

    # 3. Negotiation Emails
    if row.negotiation_count and row.negotiation_count > 0:
        summaries.append({
            "id": f"ne-{customer_external_id[:8]}",
            "customerId": customer_external_id,
            "eventName": "negotiation_email_sent",
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "eventsQuantity": int(row.negotiation_count),
            "subtotal": int(row.negotiation_count) * 500,  # €5 per email
            "currency": "EUR",
        })

    # 4. AI Processing Volume
    if row.total_count > 0:
        summaries.append({
            "id": f"pv-{customer_external_id[:8]}",
            "customerId": customer_external_id,
            "eventName": "invoices_processed",
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "eventsQuantity": row.total_count,
            "subtotal": _to_cents(row.total_sum),
            "currency": "EUR",
        })

    return {
        "status": "success",
        "data": {"usageSummary": summaries},
    }


@router.get("/invoices/{customer_external_id}")
async def proxy_invoices(
    customer_external_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return invoices for a vendor — Paid.ai first, local DB fallback."""

    # 1) Try Paid.ai SDK
    paid_invoices = await _fetch_paid_invoices(customer_external_id)
    if paid_invoices is not None:
        logger.info("Serving %d invoices from Paid.ai for %s", len(paid_invoices), customer_external_id)
        return {"status": "success", "data": paid_invoices}

    # 2) Fallback: local database
    try:
        vendor_uuid = uuid.UUID(customer_external_id)
    except ValueError:
        return {"status": "success", "data": []}

    rows = (
        await db.execute(
            select(Invoice)
            .where(Invoice.vendor_id == vendor_uuid)
            .order_by(Invoice.created_at.desc())
        )
    ).scalars().all()

    invoices = []
    for idx, inv in enumerate(rows, start=1):
        if inv.status in ("approved", "paid"):
            payment_status = "paid"
        elif inv.status in ("rejected", "overcharge"):
            payment_status = "unpaid"
        else:
            payment_status = "pending"

        issue_date = inv.created_at
        due_date = inv.due_date or (issue_date + timedelta(days=30) if issue_date else None)

        # Total from column; fall back to extracted_data JSONB
        total = inv.total
        currency = inv.currency or "EUR"
        if total is None and inv.extracted_data:
            total = inv.extracted_data.get("total")
            currency = inv.extracted_data.get("currency", currency)

        invoices.append({
            "id": str(inv.id),
            "number": idx,
            "paymentStatus": payment_status,
            "issueDate": issue_date.isoformat() if issue_date else None,
            "dueDate": due_date.isoformat() if due_date else None,
            "invoiceTotal": _to_cents(total),
            "currency": currency,
        })

    logger.info("Serving %d invoices from local DB for %s", len(invoices), customer_external_id)
    return {"status": "success", "data": invoices}


def _empty_response(customer_id: str) -> dict:
    return {
        "status": "success",
        "data": {"usageSummary": [], "orders": [], "invoices": []},
        "message": f"No usage data for customer {customer_id}",
    }

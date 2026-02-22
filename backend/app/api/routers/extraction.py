from __future__ import annotations

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.cloud_pricing import CloudPricing
from app.models.invoice import Invoice
from app.models.item import Item
from app.models.vendor import Vendor
from processing_layer.extraction.invoice import InvoiceExtractor
from processing_layer.prompts import INVOICE_ANALYSIS_PROMPT
from processing_layer.routing.decision import decide
from processing_layer.rubric.evaluator import evaluate_rubric
from processing_layer.schemas.analysis import InvoiceAnalysis
from processing_layer.llm.factory import get_provider
from processing_layer.schemas.invoice import InvoiceExtraction
from processing_layer.schemas.result import InvoiceAction
from processing_layer.schemas.rubric import InvoiceRubric
from processing_layer.schemas.signals import PriceSignal, SignalScope, SignalType

load_dotenv()

router = APIRouter(prefix="/extraction", tags=["extraction"])
logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}
DEFAULT_VENDOR_NAME = "Unknown Vendor"
PLACEHOLDER_VENDOR_NAMES = {
    "cloud services provider ltd.",
    "cloud services provider ltd",
    "cloud services ltd.",
    "cloud services ltd",
}


def _exception_message(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        return exc.__class__.__name__
    return message[:300]


@router.post("/")
async def extract_invoice(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    1) Gemini call #1: extract invoice fields from PDF/image.
    2) Persist vendor + invoice + invoice items in PostgreSQL.
    3) Query vendor invoices + cloud_pricing context.
    4) Gemini call #2: second-pass risk assessment on combined DB context.
    5) Persist second-pass result back onto the invoice.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    loop = asyncio.get_event_loop()
    try:
        provider = get_provider("gemini")
    except Exception as exc:
        logger.exception("Failed to initialize extraction provider")
        raise HTTPException(
            status_code=503,
            detail=f"Extraction provider unavailable: {_exception_message(exc)}",
        ) from exc

    extractor = InvoiceExtractor(provider)

    is_pdf = file.content_type == "application/pdf"

    try:
        if is_pdf:
            extraction = await loop.run_in_executor(
                _executor,
                extractor.extract_from_pdf,
                file_bytes,
            )
        else:
            extraction = await loop.run_in_executor(
                _executor,
                extractor.extract_from_image,
                file_bytes,
                file.content_type,
            )
    except Exception as exc:
        logger.exception("Invoice extraction failed for file %s", file.filename)
        raise HTTPException(
            status_code=502,
            detail=f"Invoice extraction failed: {_exception_message(exc)}",
        ) from exc

    extraction = extraction.model_copy(
        update={
            "vendor_name": _normalize_vendor_name(extraction.vendor_name),
            "vendor_address": _normalize_optional_text(extraction.vendor_address),
            "client_name": _normalize_optional_text(extraction.client_name),
            "client_address": _normalize_optional_text(extraction.client_address),
        }
    )

    vendor = await _get_or_create_vendor(
        db=db,
        vendor_name=extraction.vendor_name,
        vendor_address=extraction.vendor_address,
    )

    invoice = await _create_invoice_with_items(
        db=db,
        extraction=extraction,
        vendor=vendor,
    )
    await _refresh_vendor_metrics(db=db, vendor=vendor)

    # Persist first Gemini extraction before second call to avoid losing primary data.
    await db.commit()
    await db.refresh(invoice)
    await db.refresh(vendor)
    vendor_payload = {
        "id": str(vendor.id),
        "name": vendor.name,
        "vendor_address": vendor.vendor_address,
    }
    invoice_payload = {
        "id": str(invoice.id),
        "vendor_id": str(invoice.vendor_id) if invoice.vendor_id else None,
        "invoice_number": invoice.invoice_number,
        "status": invoice.status,
        "confidence_score": invoice.confidence_score,
    }

    pricing_limit = _get_pricing_limit()
    context_payload = await _build_vendor_context_payload(
        db=db,
        vendor=vendor,
        pricing_limit=pricing_limit,
    )

    second_pass: dict[str, Any] | None = None
    second_pass_error: str | None = None
    try:
        signals = _compute_signals(
            extraction=extraction,
            context_payload=context_payload,
            current_invoice_id=invoice_payload["id"],
        )
        rubric = evaluate_rubric(extraction=extraction, signals=signals, grader=provider)
        second_prompt = _build_second_pass_prompt(
            extraction=extraction,
            signals=signals,
            rubric=rubric,
        )

        analysis = await loop.run_in_executor(
            _executor,
            provider.generate_structured,
            second_prompt,
            InvoiceAnalysis,
        )
        analysis = analysis.model_copy(update={"signals": signals})
        decision = decide(analysis=analysis, confidence_score=rubric.total_score, rubric=rubric)

        invoice.anomalies = [a.model_dump(mode="json") for a in analysis.anomaly_flags]
        invoice.market_benchmarks = {
            "pricing_records_considered": len(context_payload["cloud_pricing"]),
            "pricing_vendor_filter": context_payload["pricing_vendor_filter"],
            "decision": decision.model_dump(mode="json"),
            "rubric": rubric.model_dump(mode="json"),
        }
        invoice.confidence_score = _normalize_confidence_score(rubric.total_score)
        invoice.status = _invoice_status_from_action(decision.action)
        invoice.claude_summary = analysis.summary
        invoice.updated_at = datetime.now(timezone.utc)
        await _refresh_vendor_metrics(db=db, vendor=vendor)
        await db.commit()
        await db.refresh(invoice)
        await db.refresh(vendor)

        second_pass = {
            "analysis": analysis.model_dump(mode="json"),
            "rubric": rubric.model_dump(mode="json"),
            "decision": decision.model_dump(mode="json"),
            "confidence_score": invoice.confidence_score,
        }
        invoice_payload = {
            "id": str(invoice.id),
            "vendor_id": str(invoice.vendor_id) if invoice.vendor_id else None,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "confidence_score": invoice.confidence_score,
        }
    except Exception as exc:  # pragma: no cover - network/provider failures are expected runtime possibilities.
        await db.rollback()
        second_pass_error = str(exc)
        logger.exception("Second Gemini pass failed for invoice %s", invoice_payload["id"])

    return {
        "vendor": vendor_payload,
        "invoice": invoice_payload,
        "extraction": extraction.model_dump(mode="json"),
        "vendor_context": context_payload,
        "second_pass": second_pass,
        "second_pass_error": second_pass_error,
    }


async def _get_or_create_vendor(
    db: AsyncSession,
    vendor_name: str | None,
    vendor_address: str | None,
) -> Vendor:
    name = _normalize_vendor_name(vendor_name)
    name_key = name.casefold()
    result = await db.execute(select(Vendor).where(func.lower(Vendor.name) == name_key))
    vendor = result.scalar_one_or_none()
    address = _normalize_optional_text(vendor_address)

    if vendor is None:
        vendor = Vendor(
            name=name,
            category="computing",
            vendor_address=address,
        )
        db.add(vendor)
        await db.flush()
    elif address and not vendor.vendor_address:
        vendor.vendor_address = address
        await db.flush()

    return vendor


async def _create_invoice_with_items(
    db: AsyncSession,
    extraction: InvoiceExtraction,
    vendor: Vendor,
) -> Invoice:
    invoice = Invoice(
        vendor_id=vendor.id,
        invoice_number=extraction.invoice_number,
        due_date=_parse_datetime(extraction.due_date),
        vendor_name=vendor.name,
        vendor_address=extraction.vendor_address or vendor.vendor_address,
        client_name=extraction.client_name,
        client_address=extraction.client_address,
        subtotal=_to_decimal(extraction.subtotal),
        tax=_to_decimal(extraction.tax),
        total=_to_decimal(extraction.total),
        currency=extraction.currency,
        extracted_data=extraction.model_dump(mode="json"),
        status="pending",
    )
    db.add(invoice)
    await db.flush()

    for line_item in extraction.line_items:
        db.add(
            Item(
                invoice_id=invoice.id,
                description=line_item.description,
                quantity=_to_decimal(line_item.quantity),
                unit_price=_to_decimal(line_item.unit_price),
                total_price=_to_decimal(line_item.total_price),
                unit=line_item.unit,
            )
        )
    await db.flush()
    return invoice


async def _refresh_vendor_metrics(db: AsyncSession, vendor: Vendor) -> None:
    result = await db.execute(
        select(
            func.count(Invoice.id),
            func.avg(Invoice.total),
            func.avg(func.coalesce(Invoice.confidence_score, 0)),
        ).where(Invoice.vendor_id == vendor.id)
    )
    invoice_count, avg_invoice_amount, avg_confidence_score = result.one()

    vendor.invoice_count = int(invoice_count or 0)
    vendor.avg_invoice_amount = avg_invoice_amount

    if vendor.invoice_count == 0:
        vendor.trust_score = Decimal("0.5")
    else:
        avg_confidence_decimal = _to_decimal(avg_confidence_score) or Decimal("0")
        bounded_confidence = max(Decimal("0"), min(Decimal("100"), avg_confidence_decimal))
        vendor.trust_score = bounded_confidence / Decimal("100")

    await db.flush()


async def _build_vendor_context_payload(
    db: AsyncSession,
    vendor: Vendor,
    pricing_limit: int,
) -> dict[str, Any]:
    invoices_result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.vendor_id == vendor.id)
        .order_by(Invoice.created_at.desc())
    )
    invoices = list(invoices_result.scalars().all())

    pricing_vendor = _infer_cloud_vendor(vendor.name)
    pricing_query = select(CloudPricing).order_by(CloudPricing.updated_at.desc()).limit(pricing_limit)
    if pricing_vendor:
        pricing_query = pricing_query.where(CloudPricing.vendor == pricing_vendor)
    pricing_result = await db.execute(pricing_query)
    pricing_rows = list(pricing_result.scalars().all())

    return {
        "vendor": {
            "id": str(vendor.id),
            "name": vendor.name,
            "vendor_address": vendor.vendor_address,
        },
        "invoices": [_invoice_to_context_payload(i) for i in invoices],
        "cloud_pricing": [_pricing_to_context_payload(p) for p in pricing_rows],
        "pricing_vendor_filter": pricing_vendor,
    }


def _invoice_to_context_payload(invoice: Invoice) -> dict[str, Any]:
    return {
        "id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "subtotal": _decimal_or_none(invoice.subtotal),
        "tax": _decimal_or_none(invoice.tax),
        "total": _decimal_or_none(invoice.total),
        "currency": invoice.currency,
        "status": invoice.status,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        "line_items": [
            {
                "description": item.description,
                "quantity": _decimal_or_none(item.quantity),
                "unit_price": _decimal_or_none(item.unit_price),
                "total_price": _decimal_or_none(item.total_price),
                "unit": item.unit,
            }
            for item in invoice.items
        ],
    }


def _pricing_to_context_payload(row: CloudPricing) -> dict[str, Any]:
    return {
        "vendor": row.vendor,
        "service_name": row.service_name,
        "category": row.category,
        "sku_id": row.sku_id,
        "region": row.region,
        "instance_type": row.instance_type,
        "price_per_unit": _decimal_or_none(row.price_per_unit),
        "price_per_hour": _decimal_or_none(row.price_per_hour),
        "unit": row.unit,
        "currency": row.currency,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _parse_datetime(raw_value: str | None) -> datetime | None:
    if not raw_value:
        return None
    text = raw_value.strip()
    if not text:
        return None

    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    try:
        parsed_date = date.fromisoformat(text)
        return datetime(parsed_date.year, parsed_date.month, parsed_date.day, tzinfo=timezone.utc)
    except ValueError:
        return None


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _decimal_or_none(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _infer_cloud_vendor(vendor_name: str | None) -> str | None:
    if not vendor_name:
        return None
    name = vendor_name.lower()
    if "aws" in name or "amazon" in name:
        return "aws"
    if "azure" in name or "microsoft" in name:
        return "azure"
    if "gcp" in name or "google" in name:
        return "gcp"
    return None


def _get_pricing_limit() -> int:
    raw = os.getenv("PRICING_MAX_RECORDS", "5")
    try:
        value = int(raw)
    except ValueError:
        value = 5
    return max(1, min(value, 100))


def _build_second_pass_prompt(
    extraction: InvoiceExtraction,
    signals: list[PriceSignal],
    rubric: InvoiceRubric,
) -> str:
    signals_text = "\n".join(f"- {s.statement}" for s in signals) or "No quantitative signals available."
    anomalous_signals_text = "\n".join(f"- {s.statement}" for s in signals if s.is_anomalous) or "None."
    return INVOICE_ANALYSIS_PROMPT.format(
        invoice_json=extraction.model_dump_json(indent=2),
        signals_text=signals_text,
        anomalous_signals_text=anomalous_signals_text,
        confidence_score=rubric.total_score,
    )


def _compute_signals(
    extraction: InvoiceExtraction,
    context_payload: dict[str, Any],
    current_invoice_id: str,
) -> list[PriceSignal]:
    signals: list[PriceSignal] = []
    prior_invoices = [i for i in context_payload.get("invoices", []) if i.get("id") != current_invoice_id]

    duplicate_count = 0
    if extraction.invoice_number:
        duplicate_count = sum(
            1 for inv in context_payload.get("invoices", [])
            if inv.get("invoice_number") == extraction.invoice_number
        )
    if duplicate_count > 1:
        signals.append(
            PriceSignal(
                signal_type=SignalType.DUPLICATE_INVOICE,
                scope=SignalScope.INVOICE,
                statement=(
                    f"Invoice number {extraction.invoice_number} appears {duplicate_count} times for this vendor."
                ),
                is_anomalous=True,
            )
        )

    pricing_rows = context_payload.get("cloud_pricing", [])
    for line_item in extraction.line_items:
        market_ref = _find_market_reference_price(line_item.description, pricing_rows)
        if market_ref is not None and market_ref > 0:
            deviation_pct = ((line_item.unit_price - market_ref) / market_ref) * 100.0
            signals.append(
                PriceSignal(
                    signal_type=SignalType.MARKET_DEVIATION,
                    scope=SignalScope.LINE_ITEM,
                    line_item_description=line_item.description,
                    invoice_value=line_item.unit_price,
                    reference_value=market_ref,
                    deviation_pct=deviation_pct,
                    statement=(
                        f"{line_item.description}: billed {line_item.unit_price:.6f} "
                        f"vs market {market_ref:.6f} ({deviation_pct:+.2f}%)."
                    ),
                    is_anomalous=abs(deviation_pct) > 15.0,
                )
            )

        historical_ref = _find_historical_reference_price(line_item.description, prior_invoices)
        if historical_ref is not None and historical_ref > 0:
            deviation_pct = ((line_item.unit_price - historical_ref) / historical_ref) * 100.0
            signals.append(
                PriceSignal(
                    signal_type=SignalType.HISTORICAL_DEVIATION,
                    scope=SignalScope.LINE_ITEM,
                    line_item_description=line_item.description,
                    invoice_value=line_item.unit_price,
                    reference_value=historical_ref,
                    deviation_pct=deviation_pct,
                    statement=(
                        f"{line_item.description}: billed {line_item.unit_price:.6f} "
                        f"vs historical {historical_ref:.6f} ({deviation_pct:+.2f}%)."
                    ),
                    is_anomalous=abs(deviation_pct) > 15.0,
                )
            )

    if extraction.total is not None and prior_invoices:
        historical_totals = [
            _to_float(inv.get("total"))
            for inv in prior_invoices
            if inv.get("total") is not None
        ]
        historical_totals = [v for v in historical_totals if v is not None]
        if historical_totals:
            reference_total = sum(historical_totals) / len(historical_totals)
            if reference_total > 0:
                deviation_pct = ((float(extraction.total) - reference_total) / reference_total) * 100.0
                signals.append(
                    PriceSignal(
                        signal_type=SignalType.VENDOR_TOTAL_DRIFT,
                        scope=SignalScope.INVOICE,
                        invoice_value=float(extraction.total),
                        reference_value=reference_total,
                        deviation_pct=deviation_pct,
                        statement=(
                            f"Invoice total {float(extraction.total):.2f} vs vendor historical mean "
                            f"{reference_total:.2f} ({deviation_pct:+.2f}%)."
                        ),
                        is_anomalous=abs(deviation_pct) > 25.0,
                    )
                )

    return signals


def _find_market_reference_price(description: str, pricing_rows: list[dict[str, Any]]) -> float | None:
    description_lc = description.lower()
    for row in pricing_rows:
        service_name = str(row.get("service_name") or "").lower()
        sku_id = str(row.get("sku_id") or "").lower()
        if (
            service_name
            and (service_name in description_lc or description_lc in service_name)
        ) or (sku_id and sku_id in description_lc):
            candidate = _to_float(row.get("price_per_unit")) or _to_float(row.get("price_per_hour"))
            if candidate is not None and candidate > 0:
                return candidate
    return None


def _find_historical_reference_price(description: str, invoices: list[dict[str, Any]]) -> float | None:
    target = description.strip().lower()
    samples: list[float] = []
    for invoice in invoices:
        for line_item in invoice.get("line_items", []):
            candidate_desc = str(line_item.get("description") or "").strip().lower()
            if candidate_desc != target:
                continue
            unit_price = _to_float(line_item.get("unit_price"))
            if unit_price is not None and unit_price > 0:
                samples.append(unit_price)
    if not samples:
        return None
    return sum(samples) / len(samples)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _invoice_status_from_action(action: InvoiceAction) -> str:
    if action == InvoiceAction.APPROVED:
        return "approved"
    if action == InvoiceAction.HUMAN_REVIEW:
        return "flagged"
    return "flagged"


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _normalize_vendor_name(vendor_name: str | None) -> str:
    normalized = _normalize_optional_text(vendor_name)
    if normalized is None:
        return DEFAULT_VENDOR_NAME
    if normalized.casefold() in PLACEHOLDER_VENDOR_NAMES:
        return DEFAULT_VENDOR_NAME
    return normalized


def _normalize_confidence_score(value: Any) -> int:
    numeric = _to_float(value)
    if numeric is None:
        return 0
    return max(0, min(100, int(round(numeric))))

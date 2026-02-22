from __future__ import annotations

from typing import Any

from ..schemas.invoice import InvoiceExtraction
from ..schemas.signals import PriceSignal, SignalScope, SignalType


def compute_signals(
    extraction: InvoiceExtraction,
    context: dict,
    current_invoice_id: str,
) -> list[PriceSignal]:
    """Deterministic entry point: computes all quantitative signals for an invoice."""
    signals: list[PriceSignal] = []
    prior_invoices = [i for i in context.get("invoices", []) if i.get("id") != current_invoice_id]

    duplicate_count = 0
    if extraction.invoice_number:
        duplicate_count = sum(
            1 for inv in context.get("invoices", [])
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

    pricing_rows = context.get("cloud_pricing", [])
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

    if extraction.total is not None and extraction.line_items:
        line_sum = sum(item.total_price for item in extraction.line_items)
        tax = extraction.tax or 0.0
        expected = line_sum + tax
        if abs(expected - float(extraction.total)) > 0.02:
            deviation_pct = ((float(extraction.total) - expected) / expected * 100) if expected else 0.0
            signals.append(
                PriceSignal(
                    signal_type=SignalType.MATH_INCONSISTENCY,
                    scope=SignalScope.INVOICE,
                    invoice_value=float(extraction.total),
                    reference_value=expected,
                    deviation_pct=deviation_pct,
                    statement=(
                        f"Invoice total {float(extraction.total):.2f} does not match "
                        f"sum of line items + tax ({expected:.2f}, diff {float(extraction.total) - expected:+.2f}). "
                        f"Possible extraction error or undisclosed charge."
                    ),
                    is_anomalous=True,
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

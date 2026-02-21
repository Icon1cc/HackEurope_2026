from __future__ import annotations

from ..schemas.invoice import InvoiceExtraction
from .schema import PriceSignal

ANOMALY_THRESHOLD_PCT = 15.0


def compute_signals(extraction: InvoiceExtraction, context: dict) -> list[PriceSignal]:
    """
    Deterministic entry point: computes all quantitative signals for an invoice.
    Called by InvoiceAnalyzer before the LLM synthesis step.

    TODO: implement once tool return shapes are confirmed:
      - _market_deviation(item, market_data)      needs MarketDataTool.get_spot_price() shape
      - _historical_deviation(item, history)      needs SqlDatabaseTool.fetch_invoice_history() shape
      - _duplicate_check(invoice_number, history) needs SqlDatabaseTool.fetch_invoice_history() shape
      - _vendor_total_drift(total, history)       needs SqlDatabaseTool.fetch_invoice_history() shape
    """
    raise NotImplementedError(
        "compute_signals: TODO — implement sub-signal functions once tool return shapes are known. "
        "See TODO comments above for each required sub-function."
    )

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SignalType(str, Enum):
    MARKET_DEVIATION = "market_deviation"
    HISTORICAL_DEVIATION = "historical_deviation"
    DUPLICATE_INVOICE = "duplicate_invoice"
    VENDOR_TOTAL_DRIFT = "vendor_total_drift"
    MATH_INCONSISTENCY = "math_inconsistency"


class SignalScope(str, Enum):
    LINE_ITEM = "line_item"
    INVOICE = "invoice"


class PriceSignal(BaseModel):
    signal_type: SignalType
    scope: SignalScope
    line_item_description: str | None = Field(
        default=None,
        description="Line item this signal applies to. Null for invoice-scoped signals.",
    )
    invoice_value: float | None = None
    reference_value: float | None = None
    deviation_pct: float | None = Field(
        default=None,
        description="(invoice_value - reference_value) / reference_value * 100.",
    )
    zscore: float | None = None
    n_samples: int | None = None
    statement: str = Field(
        description="Human-readable finding, e.g. 'Copper Wire 18% above avg (n=12, z=2.1)'."
    )
    is_anomalous: bool = Field(
        description="True if signal exceeds anomaly threshold (deterministic, not LLM-assigned)."
    )

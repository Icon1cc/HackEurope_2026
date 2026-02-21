from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .invoice import InvoiceExtraction, LineItem
from ..signals.schema import PriceSignal


class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AnomalyFlag(BaseModel):
    anomaly_type: str = Field(
        description="Type of anomaly, e.g. 'overpricing', 'duplicate_invoice_id', 'price_deviation'."
    )
    severity: AnomalySeverity
    affected_field: str = Field(description="Path to the affected field, e.g. 'line_items[2].unit_price'.")
    description: str = Field(description="Human-readable explanation of the anomaly.")
    confidence: float = Field(description="Confidence in this flag, 0.0 (uncertain) to 1.0 (certain).")


class LineItemAnalysis(BaseModel):
    line_item: LineItem
    flagged: bool = Field(
        description="True if any signal for this line item is anomalous. Set by LLM guided by signal statements."
    )


class InvoiceAnalysis(BaseModel):
    extraction: InvoiceExtraction
    signals: list[PriceSignal] = Field(
        default_factory=list,
        description=(
            "Deterministic quantitative signals computed before LLM synthesis. "
            "Injected post-generation — not produced by the LLM."
        ),
    )
    confidence_score: int = Field(
        description=(
            "Business-as-usual confidence score 0–100. "
            "100 = invoice looks completely normal, 0 = highly suspicious. "
            "TODO: derive from weighted signal criteria once scoring rules are defined."
        )
    )
    is_duplicate: bool = Field(description="True if this invoice appears to be a duplicate of a prior invoice.")
    duplicate_evidence: str | None = Field(
        description="Evidence of duplication, e.g. 'Found invoice #X123 on 2025-01-10 same vendor, same total'. Null if not duplicate."
    )
    line_item_analyses: list[LineItemAnalysis]
    anomaly_flags: list[AnomalyFlag]
    summary: str = Field(description="2-3 sentence plain-language summary addressed to a human auditor.")

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class CriterionId(str, Enum):
    FORMAL_VALIDITY = "formal_validity"              # invoice-level: required fields, dates, no duplicate
    MARKET_PRICE_ALIGNED = "market_price_aligned"
    HISTORICAL_PRICE_CONSISTENT = "historical_price_consistent"
    VENDOR_TOTAL_DRIFT = "vendor_total_drift"           # invoice-level: total vs historical mean


class CriterionVerdict(BaseModel):
    fulfilled: bool
    explanation: str


class CriterionResult(BaseModel):
    criterion_id: CriterionId
    line_item_description: str
    verdict: CriterionVerdict | None  # None = data unavailable
    points_awarded: float             # 0 or max_points; 0 if no data
    max_points: float                 # needed for denominator in aggregate_score
    data_available: bool              # False if tool returned nothing


class InvoiceRubric(BaseModel):
    criterion_results: list[CriterionResult]
    total_score: int  # 0–100, deterministically aggregated

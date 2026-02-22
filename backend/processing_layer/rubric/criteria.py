from __future__ import annotations

from dataclasses import dataclass, field

from ..schemas.rubric import CriterionId


@dataclass
class Criterion:
    id: CriterionId
    max_points: float          # weights must sum to 100
    prompt_key: str            # key into prompts.py for the judge prompt
    is_invoice_level: bool = field(default=False)  # True = evaluated once per invoice, not per line item


CRITERIA: list[Criterion] = [
    Criterion(CriterionId.FORMAL_VALIDITY,            20.0, "JUDGE_FORMAL_VALIDITY",  is_invoice_level=True),
    Criterion(CriterionId.MARKET_PRICE_ALIGNED,       27.0, "JUDGE_MARKET_PRICE"),
    Criterion(CriterionId.HISTORICAL_PRICE_CONSISTENT, 27.0, "JUDGE_HISTORICAL_PRICE"),
    Criterion(CriterionId.VENDOR_TOTAL_DRIFT,          26.0, "JUDGE_VENDOR_TOTAL_DRIFT", is_invoice_level=True),
]

assert abs(sum(c.max_points for c in CRITERIA) - 100.0) < 1e-9, (
    f"Criterion weights must sum to 100, got {sum(c.max_points for c in CRITERIA)}"
)

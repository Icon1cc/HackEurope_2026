from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, computed_field

from .analysis import InvoiceAnalysis
from .rubric import InvoiceRubric


class InvoiceAction(str, Enum):
    APPROVED = "approved"
    HUMAN_REVIEW = "human_review"
    ESCALATE_NEGOTIATION = "escalate_negotiation"


class InvoiceDecision(BaseModel):
    action: InvoiceAction
    reason: str = Field(description="Brief explanation of why this action was chosen.")


class NegotiationDraft(BaseModel):
    subject: str = Field(description="Email subject line.")
    body: str = Field(description="Full email body addressed to the vendor.")
    key_points: list[str] = Field(description="Bullet points of anomalies/overpricing to raise.")


class InvoiceResult(BaseModel):
    analysis: InvoiceAnalysis
    decision: InvoiceDecision
    rubric: InvoiceRubric
    negotiation_draft: NegotiationDraft | None = Field(
        default=None,
        description="Present only when action=ESCALATE_NEGOTIATION.",
    )

    @computed_field
    @property
    def confidence_score(self) -> int:
        return self.rubric.total_score

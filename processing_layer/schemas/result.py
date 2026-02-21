from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .analysis import InvoiceAnalysis


class InvoiceAction(str, Enum):
    APPROVED = "approved"
    ESCALATE_NEGOTIATION = "escalate_negotiation"
    # extensible — add further actions here as needed


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
    negotiation_draft: NegotiationDraft | None = Field(
        default=None,
        description="Present only when action=ESCALATE_NEGOTIATION.",
    )

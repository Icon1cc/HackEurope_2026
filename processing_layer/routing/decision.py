from __future__ import annotations

from ..constants import ESCALATION_CONFIDENCE_THRESHOLD
from ..schemas.analysis import InvoiceAnalysis
from ..schemas.result import InvoiceAction, InvoiceDecision


def decide(analysis: InvoiceAnalysis) -> InvoiceDecision:
    """Deterministic routing — no LLM. Returns the action to take for this invoice."""
    if analysis.is_duplicate:
        return InvoiceDecision(
            action=InvoiceAction.ESCALATE_NEGOTIATION,
            reason="Duplicate invoice detected.",
        )
    if analysis.confidence_score < ESCALATION_CONFIDENCE_THRESHOLD:
        return InvoiceDecision(
            action=InvoiceAction.ESCALATE_NEGOTIATION,
            reason=f"Confidence score {analysis.confidence_score} below threshold {ESCALATION_CONFIDENCE_THRESHOLD}.",
        )
    return InvoiceDecision(
        action=InvoiceAction.APPROVED,
        reason="No anomalies detected.",
    )

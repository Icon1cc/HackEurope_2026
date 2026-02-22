from __future__ import annotations

from ..constants import APPROVAL_THRESHOLD, ESCALATION_THRESHOLD
from ..schemas.analysis import InvoiceAnalysis
from ..schemas.result import InvoiceAction, InvoiceDecision
from ..schemas.rubric import CriterionId, InvoiceRubric


def decide(analysis: InvoiceAnalysis, confidence_score: int, rubric: InvoiceRubric) -> InvoiceDecision:
    """Deterministic routing — no LLM. Returns the action to take for this invoice."""
    formal_failed = any(
        r.criterion_id == CriterionId.FORMAL_VALIDITY
        and r.data_available
        and (r.verdict is None or not r.verdict.fulfilled)
        for r in rubric.criterion_results
    )

    if analysis.is_duplicate or confidence_score < ESCALATION_THRESHOLD:
        return InvoiceDecision(
            action=InvoiceAction.ESCALATE_NEGOTIATION,
            reason=(
                "Duplicate invoice detected."
                if analysis.is_duplicate
                else f"Confidence score {confidence_score} below escalation threshold {ESCALATION_THRESHOLD}."
            ),
        )
    # formal_failed → ALWAYS at least HUMAN_REVIEW, score is irrelevant
    if formal_failed or confidence_score < APPROVAL_THRESHOLD:
        return InvoiceDecision(
            action=InvoiceAction.HUMAN_REVIEW,
            reason=(
                "Formal validity check failed (missing required fields, invalid dates, or duplicate invoice ID)."
                if formal_failed
                else f"Confidence score {confidence_score} requires human review (threshold {APPROVAL_THRESHOLD})."
            ),
        )
    return InvoiceDecision(
        action=InvoiceAction.APPROVED,
        reason="No anomalies detected.",
    )

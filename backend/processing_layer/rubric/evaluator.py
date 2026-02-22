from __future__ import annotations

from datetime import date

from ..llm.base import LLMProvider
from ..schemas.invoice import InvoiceExtraction, LineItem
from ..schemas.rubric import (
    CriterionId,
    CriterionResult,
    CriterionVerdict,
    InvoiceRubric,
)
from ..schemas.signals import PriceSignal, SignalType
from .criteria import CRITERIA, Criterion
from .scoring import aggregate_score


def evaluate_rubric(
    extraction: InvoiceExtraction,
    signals: list[PriceSignal],
    grader: LLMProvider,
) -> InvoiceRubric:
    """Build invoice rubric from deterministic signals and formal checks."""
    context = {
        "extraction": extraction,
        "signals": signals,
    }
    results: list[CriterionResult] = []
    for criterion in CRITERIA:
        if criterion.is_invoice_level:
            results.append(evaluate_criterion(criterion, None, context, grader))
        else:
            for line_item in extraction.line_items:
                results.append(evaluate_criterion(criterion, line_item, context, grader))

    return InvoiceRubric(
        criterion_results=results,
        total_score=aggregate_score(results),
    )


def evaluate_criterion(
    criterion: Criterion,
    line_item: LineItem | None,   # None for invoice-level criteria (is_invoice_level=True)
    context: dict,
    grader: LLMProvider,
) -> CriterionResult:
    """Evaluate one criterion deterministically using extraction + signal context."""
    _ = grader  # reserved for future LLM-judge mode
    extraction = context.get("extraction")
    signals = context.get("signals") or []
    if not isinstance(signals, list):
        signals = []

    if criterion.id == CriterionId.VENDOR_TOTAL_DRIFT:
        signal = next(
            (s for s in signals if isinstance(s, PriceSignal) and s.signal_type == SignalType.VENDOR_TOTAL_DRIFT),
            None,
        )
        return _criterion_result_from_signal(
            criterion=criterion,
            line_item_description="invoice",
            signal=signal,
        )

    if criterion.id == CriterionId.FORMAL_VALIDITY:
        if not isinstance(extraction, InvoiceExtraction):
            return CriterionResult(
                criterion_id=criterion.id,
                line_item_description="invoice",
                verdict=None,
                points_awarded=0.0,
                max_points=criterion.max_points,
                data_available=False,
            )
        required_fields_ok = bool(
            extraction.invoice_number
            and extraction.vendor_name
            and extraction.total is not None
        )
        due_date_ok = extraction.due_date is None or _valid_iso_date(extraction.due_date)
        duplicate_found = any(
            isinstance(signal, PriceSignal)
            and signal.signal_type == SignalType.DUPLICATE_INVOICE
            and signal.is_anomalous
            for signal in signals
        )
        fulfilled = required_fields_ok and due_date_ok and not duplicate_found
        explanation = (
            "All formal checks passed."
            if fulfilled
            else "Missing required fields, invalid due_date, or duplicate invoice number detected."
        )
        return CriterionResult(
            criterion_id=criterion.id,
            line_item_description="invoice",
            verdict=CriterionVerdict(fulfilled=fulfilled, explanation=explanation),
            points_awarded=criterion.max_points if fulfilled else 0.0,
            max_points=criterion.max_points,
            data_available=True,
        )

    if line_item is None:
        return CriterionResult(
            criterion_id=criterion.id,
            line_item_description="invoice",
            verdict=None,
            points_awarded=0.0,
            max_points=criterion.max_points,
            data_available=False,
        )

    if criterion.id == CriterionId.MARKET_PRICE_ALIGNED:
        signal = _get_line_signal(signals, SignalType.MARKET_DEVIATION, line_item.description)
        return _criterion_result_from_signal(
            criterion=criterion,
            line_item_description=line_item.description,
            signal=signal,
        )

    if criterion.id == CriterionId.HISTORICAL_PRICE_CONSISTENT:
        signal = _get_line_signal(signals, SignalType.HISTORICAL_DEVIATION, line_item.description)
        return _criterion_result_from_signal(
            criterion=criterion,
            line_item_description=line_item.description,
            signal=signal,
        )

    raise AssertionError(f"unhandled criterion: {criterion.id}")


def _criterion_result_from_signal(
    criterion: Criterion,
    line_item_description: str,
    signal: PriceSignal | None,
) -> CriterionResult:
    if signal is None:
        return CriterionResult(
            criterion_id=criterion.id,
            line_item_description=line_item_description,
            verdict=None,
            points_awarded=0.0,
            max_points=criterion.max_points,
            data_available=False,
        )

    fulfilled = not signal.is_anomalous
    return CriterionResult(
        criterion_id=criterion.id,
        line_item_description=line_item_description,
        verdict=CriterionVerdict(fulfilled=fulfilled, explanation=signal.statement),
        points_awarded=criterion.max_points if fulfilled else 0.0,
        max_points=criterion.max_points,
        data_available=True,
    )


def _get_line_signal(
    signals: list[PriceSignal],
    signal_type: SignalType,
    line_item_description: str,
) -> PriceSignal | None:
    for signal in signals:
        if (
            isinstance(signal, PriceSignal)
            and signal.signal_type == signal_type
            and signal.line_item_description == line_item_description
        ):
            return signal
    return None


def _valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False

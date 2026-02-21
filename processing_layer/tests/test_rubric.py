"""Unit tests for rubric scoring + routing (no LLM, no network)."""
from processing_layer.rubric.scoring import aggregate_score
from processing_layer.routing.decision import decide
from processing_layer.schemas.rubric import (
    CriterionId,
    CriterionResult,
    CriterionVerdict,
    InvoiceRubric,
)
from processing_layer.schemas.analysis import InvoiceAnalysis
from processing_layer.schemas.invoice import InvoiceExtraction
from processing_layer.schemas.result import InvoiceAction


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_result(
    *,
    criterion_id: CriterionId = CriterionId.MARKET_PRICE_ALIGNED,
    fulfilled: bool,
    data_available: bool,
    max_points: float = 27.0,
) -> CriterionResult:
    return CriterionResult(
        criterion_id=criterion_id,
        line_item_description="Widget A",
        verdict=CriterionVerdict(fulfilled=fulfilled, explanation="test") if data_available else None,
        points_awarded=max_points if (fulfilled and data_available) else 0.0,
        max_points=max_points,
        data_available=data_available,
    )


def _make_rubric(*, formal_fulfilled: bool = True, formal_data_available: bool = True, score: int = 80) -> InvoiceRubric:
    return InvoiceRubric(
        criterion_results=[
            _make_result(
                criterion_id=CriterionId.FORMAL_VALIDITY,
                fulfilled=formal_fulfilled,
                data_available=formal_data_available,
                max_points=20.0,
            )
        ],
        total_score=score,
    )


def _make_analysis(*, is_duplicate: bool = False) -> InvoiceAnalysis:
    extraction = InvoiceExtraction(
        invoice_number="INV-001", invoice_date="2026-01-01", due_date=None,
        vendor_name="ACME", vendor_address=None, client_name="Client",
        client_address=None, line_items=[], subtotal=None, tax=None,
        total=None, currency=None,
    )
    return InvoiceAnalysis(
        extraction=extraction,
        signals=[],
        is_duplicate=is_duplicate,
        duplicate_evidence=None,
        line_item_analyses=[],
        anomaly_flags=[],
        summary="test",
    )


# ── aggregate_score ───────────────────────────────────────────────────────────

def test_aggregate_score_empty_returns_100():
    assert aggregate_score([]) == 100


def test_aggregate_score_all_fulfilled():
    results = [
        _make_result(fulfilled=True, data_available=True, max_points=27.0),
        _make_result(fulfilled=True, data_available=True, max_points=27.0),
        _make_result(fulfilled=True, data_available=True, max_points=26.0),
        _make_result(criterion_id=CriterionId.FORMAL_VALIDITY, fulfilled=True, data_available=True, max_points=20.0),
    ]
    assert aggregate_score(results) == 100


def test_aggregate_score_all_failed():
    results = [
        _make_result(fulfilled=False, data_available=True, max_points=27.0),
        _make_result(fulfilled=False, data_available=True, max_points=27.0),
        _make_result(fulfilled=False, data_available=True, max_points=26.0),
        _make_result(criterion_id=CriterionId.FORMAL_VALIDITY, fulfilled=False, data_available=True, max_points=20.0),
    ]
    assert aggregate_score(results) == 0


def test_aggregate_score_excludes_unavailable_from_denominator():
    # only formal (20 pts) available + fulfilled → score = 20/20 * 100 = 100
    results = [
        _make_result(criterion_id=CriterionId.FORMAL_VALIDITY, fulfilled=True, data_available=True, max_points=20.0),
        _make_result(fulfilled=False, data_available=False, max_points=27.0),
        _make_result(fulfilled=False, data_available=False, max_points=27.0),
        _make_result(fulfilled=False, data_available=False, max_points=26.0),
    ]
    assert aggregate_score(results) == 100


def test_aggregate_score_mixed():
    # 27 awarded out of 47 available (27+20) → round(27/47*100) = 57
    results = [
        _make_result(fulfilled=True,  data_available=True,  max_points=27.0),
        _make_result(criterion_id=CriterionId.FORMAL_VALIDITY, fulfilled=False, data_available=True, max_points=20.0),
        _make_result(fulfilled=False, data_available=False, max_points=27.0),
        _make_result(fulfilled=False, data_available=False, max_points=26.0),
    ]
    score = aggregate_score(results)
    assert score == round(27 / 47 * 100)


# ── routing / decide ──────────────────────────────────────────────────────────

def test_decide_approved():
    rubric = _make_rubric(formal_fulfilled=True, score=85)
    assert decide(_make_analysis(), confidence_score=85, rubric=rubric).action == InvoiceAction.APPROVED


def test_decide_human_review_low_score():
    rubric = _make_rubric(formal_fulfilled=True, score=55)
    assert decide(_make_analysis(), confidence_score=55, rubric=rubric).action == InvoiceAction.HUMAN_REVIEW


def test_decide_escalate_low_score():
    rubric = _make_rubric(formal_fulfilled=True, score=25)
    assert decide(_make_analysis(), confidence_score=25, rubric=rubric).action == InvoiceAction.ESCALATE_NEGOTIATION


def test_decide_escalate_duplicate():
    rubric = _make_rubric(formal_fulfilled=True, score=99)
    assert decide(_make_analysis(is_duplicate=True), confidence_score=99, rubric=rubric).action == InvoiceAction.ESCALATE_NEGOTIATION


def test_decide_formal_failure_forces_human_review_despite_high_score():
    # score=85 would normally → APPROVED, but formal failure → HUMAN_REVIEW
    rubric = _make_rubric(formal_fulfilled=False, score=85)
    assert decide(_make_analysis(), confidence_score=85, rubric=rubric).action == InvoiceAction.HUMAN_REVIEW


def test_decide_formal_unavailable_does_not_force_human_review():
    # formal data not available (DB stub) → no override, high score → APPROVED
    rubric = _make_rubric(formal_fulfilled=False, formal_data_available=False, score=85)
    assert decide(_make_analysis(), confidence_score=85, rubric=rubric).action == InvoiceAction.APPROVED


def test_decide_formal_failure_with_low_score_escalates():
    # both formal failure AND low score → ESCALATE wins (score check comes first)
    rubric = _make_rubric(formal_fulfilled=False, score=25)
    assert decide(_make_analysis(), confidence_score=25, rubric=rubric).action == InvoiceAction.ESCALATE_NEGOTIATION

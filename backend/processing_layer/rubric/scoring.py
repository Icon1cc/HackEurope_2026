from __future__ import annotations

from ..schemas.rubric import CriterionResult


def aggregate_score(results: list[CriterionResult]) -> int:
    """Deterministic aggregation — no LLM.

    Excludes criteria where data_available=False from denominator.
    Returns 100 if no criteria had data (no evidence of problems).
    """
    available = [r for r in results if r.data_available]
    if not available:
        return 100
    total_awarded = sum(r.points_awarded for r in available)
    total_possible = sum(r.max_points for r in available)
    assert total_possible > 0, "max_points must be > 0 for available criteria"
    return round(total_awarded / total_possible * 100)

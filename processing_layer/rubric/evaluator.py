from __future__ import annotations

from ..llm.base import LLMProvider
from ..schemas.invoice import LineItem
from ..schemas.rubric import CriterionResult
from .criteria import Criterion


def evaluate_criterion(
    criterion: Criterion,
    line_item: LineItem | None,   # None for invoice-level criteria (is_invoice_level=True)
    context: dict,
    grader: LLMProvider,
) -> CriterionResult:
    """LLM-as-judge call for a single criterion × line item (or invoice level).

    For FORMAL_VALIDITY: deterministic Python checks — no LLM needed.
      Sub-checks: mandatory fields present, date validity, no duplicate invoice ID.
      data_available=True always (field/date checks need no external data).

    For price criteria: LLM judge call using criterion.prompt_key.

    Stub: raises NotImplementedError until tool return shapes are known.
    """
    raise NotImplementedError(
        f"evaluate_criterion not implemented for {criterion.id} — "
        "tool return shapes must be defined first."
    )

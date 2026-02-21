from __future__ import annotations

from datetime import date, timedelta

from ..llm.base import LLMProvider
from ..negotiation.agent import NegotiationAgent
from ..prompts import INVOICE_ANALYSIS_PROMPT
from ..routing.decision import decide
from ..rubric import CRITERIA, aggregate_score, evaluate_criterion
from ..schemas.analysis import InvoiceAnalysis
from ..schemas.invoice import InvoiceExtraction
from ..schemas.result import InvoiceAction, InvoiceResult
from ..schemas.rubric import InvoiceRubric
from ..signals.compute import compute_signals
from ..signals.schema import PriceSignal
from ..tools.market_data import MarketDataTool
from ..tools.sql_db import SqlDatabaseTool


class InvoiceAnalyzer:
    def __init__(
        self,
        provider: LLMProvider,
        sql_tool: SqlDatabaseTool,
        market_tool: MarketDataTool,
        history_lookback_days: int = 365,
        grader_provider: LLMProvider | None = None,
    ):
        assert isinstance(provider, LLMProvider), f"provider must be LLMProvider, got {type(provider)}"
        assert isinstance(sql_tool, SqlDatabaseTool), f"sql_tool must be SqlDatabaseTool, got {type(sql_tool)}"
        assert isinstance(market_tool, MarketDataTool), f"market_tool must be MarketDataTool, got {type(market_tool)}"
        assert history_lookback_days > 0, "history_lookback_days must be positive"
        self.provider = provider
        self.grader = grader_provider if grader_provider is not None else provider
        self.sql = sql_tool
        self.market = market_tool
        self.history_lookback_days = history_lookback_days

    def process(self, extraction: InvoiceExtraction) -> InvoiceResult:
        """Full pipeline: analyze → route → optionally draft negotiation email."""
        analysis, rubric = self._run_pipeline(extraction)
        decision = decide(analysis, rubric.total_score, rubric)
        draft = None
        if decision.action == InvoiceAction.ESCALATE_NEGOTIATION:
            draft = NegotiationAgent(self.provider).draft_email(analysis)
        return InvoiceResult(analysis=analysis, decision=decision, rubric=rubric, negotiation_draft=draft)

    def analyze(self, extraction: InvoiceExtraction) -> InvoiceAnalysis:
        """Returns InvoiceAnalysis only (rubric computed but not returned)."""
        assert isinstance(extraction, InvoiceExtraction), f"Expected InvoiceExtraction, got {type(extraction)}"
        analysis, _ = self._run_pipeline(extraction)
        return analysis

    def _run_pipeline(self, extraction: InvoiceExtraction) -> tuple[InvoiceAnalysis, InvoiceRubric]:
        """Shared pipeline: context → signals → rubric → LLM analysis."""
        assert isinstance(extraction, InvoiceExtraction), f"Expected InvoiceExtraction, got {type(extraction)}"
        context = self._gather_context(extraction)
        signals = compute_signals(extraction, context)
        rubric = self._evaluate_rubric(extraction, context)
        prompt = self._build_prompt(extraction, signals, rubric)
        result = self.provider.generate_structured(prompt, InvoiceAnalysis)
        assert isinstance(result, InvoiceAnalysis), f"Unexpected result type: {type(result)}"
        analysis = result.model_copy(update={"signals": signals})
        return analysis, rubric

    def _evaluate_rubric(self, extraction: InvoiceExtraction, context: dict) -> InvoiceRubric:
        results = []
        for criterion in CRITERIA:
            if criterion.is_invoice_level:
                results.append(evaluate_criterion(criterion, None, context, self.grader))
            else:
                for item in extraction.line_items:
                    results.append(evaluate_criterion(criterion, item, context, self.grader))
        return InvoiceRubric(
            criterion_results=results,
            total_score=aggregate_score(results),
        )

    def _gather_context(self, extraction: InvoiceExtraction) -> dict:
        context: dict = {}

        if extraction.vendor_name and extraction.invoice_date:
            date_end = extraction.invoice_date
            date_start = _shift_date(date_end, -self.history_lookback_days)
            # TODO: return shape depends on SqlDatabaseTool implementation
            # expected: list of dicts each representing a past invoice with keys:
            # invoice_number, invoice_date, total, line_items (list of {description, unit_price, quantity})
            context["invoice_history"] = self.sql.fetch_invoice_history(
                vendor=extraction.vendor_name,
                date_range=(date_start, date_end),
            )

        context["market_prices"] = {}
        for item in extraction.line_items:
            symbol = _description_to_symbol(item.description)
            if symbol:
                # TODO: return shape depends on MarketDataTool implementation
                # expected: dict with at minimum {"price": float, "currency": str, "timestamp": str}
                context["market_prices"][item.description] = self.market.get_spot_price(symbol)

        return context

    def _build_prompt(self, extraction: InvoiceExtraction, signals: list[PriceSignal], rubric: InvoiceRubric) -> str:
        signals_text = "\n".join(f"- {s.statement}" for s in signals) or "No quantitative signals available."
        anomalous_text = "\n".join(f"- {s.statement}" for s in signals if s.is_anomalous) or "None."
        return INVOICE_ANALYSIS_PROMPT.format(
            invoice_json=extraction.model_dump_json(indent=2),
            signals_text=signals_text,
            anomalous_signals_text=anomalous_text,
            confidence_score=rubric.total_score,
        )


def _shift_date(iso_date: str, delta_days: int) -> str:
    """Shift ISO date string by delta_days. Raises ValueError immediately on malformed input."""
    d = date.fromisoformat(iso_date)
    return (d + timedelta(days=delta_days)).isoformat()


def _description_to_symbol(description: str) -> str | None:
    """
    Map a line item description to a commodity symbol for MarketDataTool.
    TODO: implement proper lookup (dict-based or fuzzy match) once tools are live.
    Currently returns None for all inputs — market lookup is skipped.
    """
    return None

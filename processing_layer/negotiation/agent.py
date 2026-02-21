from __future__ import annotations

from ..llm.base import LLMProvider
from ..prompts import NEGOTIATION_PROMPT
from ..schemas.analysis import InvoiceAnalysis
from ..schemas.result import NegotiationDraft


class NegotiationAgent:
    def __init__(self, provider: LLMProvider):
        assert isinstance(provider, LLMProvider), f"provider must be LLMProvider, got {type(provider)}"
        self.provider = provider

    def draft_email(self, analysis: InvoiceAnalysis) -> NegotiationDraft:
        assert isinstance(analysis, InvoiceAnalysis), f"Expected InvoiceAnalysis, got {type(analysis)}"
        prompt = NEGOTIATION_PROMPT.format(
            vendor_name=analysis.extraction.vendor_name or "the vendor",
            invoice_number=analysis.extraction.invoice_number or "N/A",
            summary=analysis.summary,
            anomaly_flags="\n".join(
                f"- [{f.severity.value.upper()}] {f.description}" for f in analysis.anomaly_flags
            ) or "See signals below.",
            signals="\n".join(
                f"- {s.statement}" for s in analysis.signals if s.is_anomalous
            ) or "No specific signals.",
        )
        result = self.provider.generate_structured(prompt, NegotiationDraft)
        assert isinstance(result, NegotiationDraft), f"Unexpected result type: {type(result)}"
        return result

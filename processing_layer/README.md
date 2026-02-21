# processing_layer

LLM-powered invoice processing — extraction, anomaly detection, confidence scoring.

## Quickstart

```bash
cp .env.example .env  # set GEMINI_API_KEY
uv sync && pytest tests/
```

## Integration

```python
from processing_layer.llm.gemini import GeminiProvider
from processing_layer.extraction.invoice import InvoiceExtractor

extractor = InvoiceExtractor(GeminiProvider())
extraction = extractor.extract_from_pdf(pdf_bytes)   # or extract_from_image(bytes, mime)
extraction.model_dump()   # serialize to dict/JSON for storage or downstream use
```

For full pipeline (requires `SqlDatabaseTool` + `MarketDataTool` implemented):

```python
from processing_layer.analysis.invoice import InvoiceAnalyzer

result = InvoiceAnalyzer(GeminiProvider(), db_tool, market_tool).process(extraction)
result.decision.action          # InvoiceAction.APPROVED | ESCALATE_NEGOTIATION
result.analysis.confidence_score  # 0–100
result.negotiation_draft        # NegotiationDraft | None — present if escalated
```

## Gemini API Calls

| Call | Input | Output |
|---|---|---|
| Extraction (image) | bytes + MIME type | `InvoiceExtraction` |
| Extraction (PDF) | bytes — File API upload/delete | `InvoiceExtraction` |
| Anomaly analysis | invoice JSON + signal statements | `InvoiceAnalysis` |
| Negotiation draft | anomaly flags + signals | `NegotiationDraft` (only if escalated) |

## Architecture

- **`llm/`** — `LLMProvider` abstraction; Gemini default, swappable
- **`schemas/`** — all Pydantic models; `InvoiceResult` is the final API response
- **`extraction/`** — document → `InvoiceExtraction`
- **`signals/`** — deterministic math on tool data → `PriceSignal` list (no LLM)
- **`analysis/`** — signals + LLM → `InvoiceAnalysis`; `process()` returns full `InvoiceResult`
- **`routing/`** — deterministic decision: `APPROVED` or `ESCALATE_NEGOTIATION`
- **`negotiation/`** — LLM drafts renegotiation email when escalated
- **`tools/`** — `SqlDatabaseTool`, `MarketDataTool` interfaces (stubs, implement to enable analysis)

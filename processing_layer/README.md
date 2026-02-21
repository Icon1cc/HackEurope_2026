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

For anomaly analysis, implement `SqlDatabaseTool` and `MarketDataTool` (subclass, fill `NotImplementedError` methods), then:

```python
from processing_layer.analysis.invoice import InvoiceAnalyzer

analysis = InvoiceAnalyzer(GeminiProvider(), db_tool, market_tool).analyze(extraction)
analysis.confidence_score   # 0–100
analysis.anomaly_flags      # list[AnomalyFlag]
analysis.summary            # plain-text auditor summary
```

## Gemini API Calls

| Call | Input | Output |
|---|---|---|
| Extraction (image) | bytes + MIME type | `InvoiceExtraction` |
| Extraction (PDF) | bytes — File API upload/delete | `InvoiceExtraction` |
| Anomaly analysis | invoice JSON + signal statements | `InvoiceAnalysis` |

## Architecture

- **`llm/`** — `LLMProvider` abstraction; Gemini default, swappable
- **`schemas/`** — all Pydantic models
- **`extraction/`** — document → `InvoiceExtraction`
- **`signals/`** — deterministic math on tool data → `PriceSignal` list (no LLM involved)
- **`analysis/`** — signals + LLM → `InvoiceAnalysis` with `confidence_score`
- **`tools/`** — `SqlDatabaseTool`, `MarketDataTool` interfaces (stubs, implement to enable analysis)

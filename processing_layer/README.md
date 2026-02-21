# processing_layer

LLM-powered document processing — structured extraction from invoices (images + PDFs).

## Architecture

- **`llm/`** — plug-in-play provider abstraction; swap models by subclassing `LLMProvider`; Gemini wired up by default
- **`schemas/`** — Pydantic models define the output shape; structured, typed results guaranteed
- **`extraction/`** — orchestrates provider + schema into a typed result; one extractor per document type
- **`analysis/`** — aggregates extraction output with DB history + market prices; single LLM call produces typed anomaly report with confidence score
- **`signals/`** — deterministic price/anomaly signal computation; pure Python math on tool outputs before LLM synthesis
- **`prompts.py`** — single source of truth for all prompt strings

## Setup

```bash
cp .env.example .env   # set GEMINI_API_KEY
uv sync
python scripts/test_invoice_extraction.py <path/to/invoice.pdf>
python scripts/test_invoice_analysis.py <path/to/invoice.pdf>
```

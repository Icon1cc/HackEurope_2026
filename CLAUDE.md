# HackEurope 2026 — Project Overview

## Subprojects

### `processing_layer/`

LLM-powered invoice processing pipeline. Takes raw invoice documents (PDF or image) and produces a structured anomaly analysis with a confidence score.

**Pipeline:**
1. **Extraction** (`extraction/`) — Gemini reads the document, returns typed `InvoiceExtraction` (line items, vendor, totals, dates)
2. **Context gathering** (`analysis/`) — fetches historical invoices from SQL DB and live market prices via tool stubs
3. **Signal computation** (`signals/`) — deterministic Python math on raw tool data; produces `PriceSignal` objects with human-readable statements (e.g. "Copper Wire 18% above avg, z=2.1")
4. **LLM synthesis** — single Gemini call receives signal statements (not raw data), returns `InvoiceAnalysis` with anomaly flags, `confidence_score` (0–100), and auditor summary
5. **Injection** — deterministic signals injected into final result post-LLM (immutable)

**Key design choices:**
- All LLM calls use `response_json_schema` + `model_validate_json` (explicit JSON Schema, no SDK magic)
- Fail-fast everywhere: assert preconditions, raise on bad state, no silent defaults
- `LLMProvider` abstraction — Gemini wired up, swappable
- Signals layer keeps math out of the LLM; LLM does reasoning, Python does arithmetic

**Current state:**
- Extraction: fully implemented
- Analysis orchestration: scaffolded, wired end-to-end
- `signals/compute.py`: stub — raises `NotImplementedError` pending tool return shape definitions
- `tools/` (`SqlDatabaseTool`, `MarketDataTool`): stubs — raise `NotImplementedError`

**Entry points:**
```bash
cd processing_layer
python scripts/test_invoice_extraction.py <invoice.pdf>
python scripts/test_invoice_analysis.py <invoice.pdf>
```

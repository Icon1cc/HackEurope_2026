# HackEurope 2026 — Project Overview

## Subprojects

### `processing_layer/`

LLM-powered invoice processing pipeline. Takes raw invoice documents (PDF or image) and produces a structured anomaly analysis with a confidence score.

**Pipeline:**
1. **Extraction** (`extraction/`) — Gemini reads the document, returns typed `InvoiceExtraction`
2. **Context gathering** (`analysis/`) — fetches historical invoices (SQL) + market prices via tool stubs
3. **Signal computation** (`signals/`) — deterministic Python math → `PriceSignal` list with human-readable statements
4. **LLM synthesis** (`analysis/`) — single Gemini call on signals → `InvoiceAnalysis` with `confidence_score` 0–100
5. **Routing** (`routing/`) — deterministic: `APPROVED` or `ESCALATE_NEGOTIATION`
6. **Negotiation** (`negotiation/`) — if escalated, Gemini drafts renegotiation email → `NegotiationDraft`
7. Final output: `InvoiceResult` (analysis + decision + optional draft)

**Gemini API calls:**

| Call | Method | Output | Conditional? |
|---|---|---|---|
| Invoice extraction (image) | `generate_structured_from_image` | `InvoiceExtraction` | — |
| Invoice extraction (PDF) | `generate_structured_from_pdf` (File API) | `InvoiceExtraction` | — |
| Anomaly analysis | `generate_structured` (signals prompt) | `InvoiceAnalysis` | — |
| Negotiation draft | `generate_structured` (anomaly prompt) | `NegotiationDraft` | only if escalated |

**Key design choices:**
- All LLM calls use `response_json_schema` + `model_validate_json` (explicit JSON Schema, no SDK magic)
- Fail-fast everywhere: assert preconditions, raise on bad state, no silent defaults
- `LLMProvider` abstraction — Gemini wired up, swappable
- Signals layer keeps math out of the LLM; LLM does reasoning, Python does arithmetic
- Routing is pure Python — no LLM in the decision path

**Current state:**
- Extraction: fully implemented
- Analysis + routing + negotiation: scaffolded end-to-end
- `signals/compute.py`: stub — raises `NotImplementedError` pending tool return shapes
- `tools/` (`SqlDatabaseTool`, `MarketDataTool`): stubs — raise `NotImplementedError`

**Entry points:**
```bash
cd processing_layer && pytest tests/
```

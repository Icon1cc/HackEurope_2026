# HackEurope 2026 — Project Overview

## Subprojects

### `processing_layer/`

LLM-powered invoice processing pipeline. Takes raw invoice documents (PDF or image) and produces a structured anomaly analysis with a rubric-based confidence score.

**Pipeline:**
1. **Extraction** (`extraction/`) — Gemini reads the document, returns typed `InvoiceExtraction`
2. **Context gathering** (`analysis/`) — fetches historical invoices (SQL) + market prices via tool stubs
3. **Signal computation** (`signals/`) — deterministic Python math → `PriceSignal` list with human-readable statements
4. **Rubric evaluation** (`rubric/`) — per-criterion judge calls → `InvoiceRubric` with `total_score` 0–100 (deterministically aggregated)
5. **LLM synthesis** (`analysis/`) — Gemini call on signals + rubric score → `InvoiceAnalysis`
6. **Routing** (`routing/`) — deterministic three-tier: `APPROVED` / `HUMAN_REVIEW` / `ESCALATE_NEGOTIATION`
7. **Negotiation** (`negotiation/`) — if escalated, Gemini drafts renegotiation email → `NegotiationDraft`
8. Final output: `InvoiceResult` (analysis + rubric + decision + optional draft + `confidence_score`)

**Gemini API calls:**

| Call | Method | Output | Conditional? |
|---|---|---|---|
| Invoice extraction (image) | `generate_structured_from_image` | `InvoiceExtraction` | — |
| Invoice extraction (PDF) | `generate_structured_from_pdf` (File API) | `InvoiceExtraction` | — |
| Judge: formal validity | `generate_structured` (judge prompt) | `CriterionVerdict` | once per invoice |
| Judge: market price | `generate_structured` (judge prompt) | `CriterionVerdict` | per line item |
| Judge: historical price | `generate_structured` (judge prompt) | `CriterionVerdict` | per line item |
| Judge: competitor price | `generate_structured` (judge prompt) | `CriterionVerdict` | per line item |
| Anomaly analysis | `generate_structured` (signals + rubric prompt) | `InvoiceAnalysis` | — |
| Negotiation draft | `generate_structured` (anomaly prompt) | `NegotiationDraft` | only if escalated |

**Key design choices:**
- All LLM calls use `response_json_schema` + `model_validate_json` (explicit JSON Schema, no SDK magic)
- Fail-fast everywhere: assert preconditions, raise on bad state, no silent defaults
- `LLMProvider` abstraction — Gemini wired up, swappable
- Signals layer keeps math out of the LLM; LLM does reasoning, Python does arithmetic
- **Rubric-based scoring**: `confidence_score` deterministically aggregated from per-criterion verdicts — not LLM-produced
- Rubric excludes criteria with no data from denominator; weight sum enforced by assertion at import
- Separate `grader_provider` for judge calls (defaults to main provider; swappable)
- Routing is pure Python — no LLM in the decision path

**Routing thresholds (`constants.py`):**
- `APPROVAL_THRESHOLD = 80` → score ≥ 80: `APPROVED`
- `ESCALATION_THRESHOLD = 40` → score < 40: `ESCALATE_NEGOTIATION`; 40–79: `HUMAN_REVIEW`
- `FORMAL_VALIDITY` failed → always `HUMAN_REVIEW` regardless of score
- `is_duplicate=True` → always `ESCALATE_NEGOTIATION`

**Rubric criteria (`rubric/criteria.py`) — weights sum to 100:**
| Criterion | Weight | Scope | Prompt key |
|---|---|---|---|
| `FORMAL_VALIDITY` | 20 pts | invoice-level | `JUDGE_FORMAL_VALIDITY` |
| `MARKET_PRICE_ALIGNED` | 27 pts | per line item | `JUDGE_MARKET_PRICE` |
| `HISTORICAL_PRICE_CONSISTENT` | 27 pts | per line item | `JUDGE_HISTORICAL_PRICE` |
| `COMPETITOR_PRICE_ALIGNED` | 26 pts | per line item | `JUDGE_COMPETITOR_PRICE` |

`FORMAL_VALIDITY` sub-checks (deterministic Python, no LLM): required fields present, date validity, no duplicate invoice ID.

**Current state:**
- Extraction: fully implemented
- Rubric schemas + scoring + criteria + routing: implemented; `evaluate_criterion`: stub (raises `NotImplementedError`)
- Analysis + negotiation: scaffolded end-to-end
- `signals/compute.py`: stub — raises `NotImplementedError` pending tool return shapes
- `tools/` (`SqlDatabaseTool`, `MarketDataTool`): stubs — raise `NotImplementedError`

**Entry points:**
```bash
cd processing_layer && pytest tests/
```

---

## Documentation rule
After any architecture change (new criteria, routing logic, schemas, pipeline steps, tool interfaces), always update:
- `processing_layer/CLAUDE.md` — keep fully up to date
- `processing_layer/README.md` — update sparsely/concisely only when relevant to understanding or extending the system

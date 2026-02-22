# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**InvoiceGuard** — B2B invoice anomaly detection platform. Ingests cloud vendor invoices, extracts data via LLM (Gemini), compares against real-time market pricing, and flags overcharges with rubric-based confidence scoring.

## Architecture

Four independent components, each with its own package manager and venv:

| Component | Stack | Port | Purpose |
|---|---|---|---|
| `backend/` | FastAPI + SQLAlchemy (async) + PostgreSQL | 8000 | REST API, data layer |
| `frontend/` | React 18 + TypeScript + Vite + Tailwind | 3000 | Web UI |
| `processing_layer/` | Gemini API + Pydantic | — | LLM invoice extraction & analysis |
| `data_sourcing/` | Playwright + httpx | — | Cloud pricing scraping |

### Backend Architecture (Clean Layered)

```
Routers → Services → Repositories → SQLAlchemy Models
   ↓          ↓           ↓
Schemas   Business    DB queries
(Pydantic) logic     (async)
```

- **Models:** Invoice, Vendor, Client, Payment, Override, Item, MarketData, CloudPricing
- **CloudPricing** is a unified catalogue across AWS/Azure/GCP with upsert-on-conflict deduplication
- **Dependencies:** FastAPI `Depends()` injection wires repos into services into routes (`app/core/dependencies.py`)
- **Database:** PostgreSQL 15 on port **5433** (not default 5432), DB name `hackeurope`

### Processing Layer Pipeline

1. **Extraction** (`extraction/`) — Gemini reads the document, returns typed `InvoiceExtraction`
2. **Context gathering** (`analysis/`) — fetches historical invoices (SQL) + market prices via tool stubs
3. **Signal computation** (`signals/`) — deterministic Python math → `PriceSignal` list with human-readable statements
4. **Rubric evaluation** (`rubric/`) — per-criterion judge calls → `InvoiceRubric` with `total_score` 0–100 (deterministically aggregated)
5. **LLM synthesis** (`analysis/`) — Gemini call on signals + rubric score → `InvoiceAnalysis`
6. **Routing** (`routing/`) — deterministic three-tier: `APPROVED` / `HUMAN_REVIEW` / `ESCALATE_NEGOTIATION`
7. **Negotiation** (`negotiation/`) — if escalated, Gemini drafts renegotiation email → `NegotiationDraft`
8. Final output: `InvoiceResult` (analysis + rubric + decision + optional draft + `confidence_score`)

**Key design choices:**
- All LLM calls use `response_json_schema` + `model_validate_json` (explicit JSON Schema, no SDK magic)
- Fail-fast everywhere: assert preconditions, raise on bad state, no silent defaults
- `LLMProvider` abstraction — Gemini wired up, swappable
- Signals layer keeps math out of the LLM; LLM does reasoning, Python does arithmetic
- **Rubric-based scoring**: `confidence_score` deterministically aggregated from per-criterion verdicts — not LLM-produced
- Routing is pure Python — no LLM in the decision path

**Routing thresholds (`constants.py`):**
- `APPROVAL_THRESHOLD = 80` → score ≥ 80: `APPROVED`
- `ESCALATION_THRESHOLD = 40` → score < 40: `ESCALATE_NEGOTIATION`; 40–79: `HUMAN_REVIEW`
- `FORMAL_VALIDITY` failed → always `HUMAN_REVIEW` regardless of score
- `is_duplicate=True` → always `ESCALATE_NEGOTIATION`

**Rubric criteria (`rubric/criteria.py`) — weights sum to 100:**

| Criterion | Weight | Scope | Signal source |
|---|---|---|---|
| `FORMAL_VALIDITY` | 20 pts | invoice-level | `DUPLICATE_INVOICE` signal + field checks |
| `MARKET_PRICE_ALIGNED` | 27 pts | per line item | `MARKET_DEVIATION` signal (needs CloudPricing match) |
| `HISTORICAL_PRICE_CONSISTENT` | 27 pts | per line item | `HISTORICAL_DEVIATION` signal (needs prior invoice match) |
| `VENDOR_TOTAL_DRIFT` | 26 pts | invoice-level | `VENDOR_TOTAL_DRIFT` signal (needs prior invoices) |

Criteria where no signal/data is found → `data_available=False` → excluded from score denominator (score = available points / available max × 100).

**`AnomalyFlag` (LLM-generated, NOT used for routing):**
- Produced by Gemini call #2 inside `InvoiceAnalysis` — LLM freely assigns `anomaly_type`, `severity`, `confidence` based on signal statements it receives
- Stored in `invoice.anomalies` for UI display and fed into negotiation email prompt
- **Routing decision uses only `rubric.total_score`, `formal_failed`, and `analysis.is_duplicate`** — `anomaly_flags` have no effect on APPROVED / HUMAN_REVIEW / ESCALATE_NEGOTIATION

**Current state (standalone processing_layer module):**
- Extraction: fully implemented
- Rubric schemas + scoring + criteria + routing: fully implemented with deterministic signal-based evaluation
- `signals/compute.py:compute_signals()`: **implemented** — computes DUPLICATE_INVOICE, MARKET_DEVIATION, HISTORICAL_DEVIATION, VENDOR_TOTAL_DRIFT signals from dict context
- Analysis + negotiation: scaffolded end-to-end; `InvoiceAnalyzer` orchestrates full pipeline but is **bypassed** by the backend extraction endpoint (backend has its own inline pipeline)
- `tools/` (`SqlDatabaseTool`, `MarketDataTool`): stubs — backend uses SQLAlchemy repos directly
- `NegotiationAgent`: fully implemented; wired to backend endpoint (runs on ESCALATE_NEGOTIATION, non-duplicate)

### Processing Layer Integration (backend `/api/v1/extraction/`)

The backend extraction endpoint uses `backend/processing_layer/` components directly but **does NOT use `InvoiceAnalyzer`** as orchestrator — it has its own 12-step inline pipeline:

| Step | Component used |
|---|---|
| 1. File validation | MIME type check inline |
| 2. Gemini call #1 | `extraction/invoice.py:InvoiceExtractor` → `InvoiceExtraction` |
| 3. Vendor upsert | SQLAlchemy repo (not tool stubs) |
| 4–5. Invoice + Items create + commit | ORM direct |
| 6. Context build | DB queries (prior invoices + CloudPricing) |
| 7. Signal computation | `signals/compute.py:compute_signals()` — dict context, returns `list[PriceSignal]` |
| 8. Rubric evaluation | `rubric/evaluator.py:evaluate_rubric()` → `InvoiceRubric` |
| 9. Gemini call #2 | `llm/gemini.py:GeminiProvider.generate_structured()` → `InvoiceAnalysis` |
| 10. Routing | `routing/decision.py:decide()` → `InvoiceDecision` |
| 11. DB update | Attach analysis + rubric + status; commit |
| 12. Response | `{vendor, invoice, extraction, vendor_context, second_pass}` |

**Bypassed / not wired:** `InvoiceAnalyzer` (backend has own inline pipeline), `SqlDatabaseTool`, `MarketDataTool`

## Common Commands

### Backend

```bash
cd backend

# Run server
uvicorn app.main:app --reload

# Database migrations
alembic revision --autogenerate -m "description"   # Generate
alembic upgrade head                                # Apply
alembic downgrade -1                                # Rollback

# Seed data (drops and recreates all tables)
python seed.py

# Tests (requires hackeurope_test DB on port 5433)
pytest                          # All tests
pytest tests/test_pricing.py    # Single file
pytest -k "test_health"         # By name
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # Dev server (port 3000)
npm run build        # Production build
npm run type-check   # TypeScript checking
```

### Processing Layer

```bash
cd processing_layer
uv sync
python tests/test_invoice_extraction.py <invoice.pdf>
python tests/test_invoice_analysis.py <invoice.pdf>
pytest tests/
```

### Data Sourcing

```bash
cd data_sourcing
uv sync
uv run python -m clients.cloud_pricing_scraper --out data/cloud_pricing.json
```

### Docker (full stack)

```bash
docker-compose up -d          # Start Postgres + Backend
docker-compose down -v        # Reset everything
```

## Environment Variables

Each component has a `.env.example`. Key variables:

- **Backend:** `DATABASE_URL` (asyncpg connection string), `GEMINI_API_KEY` (preferred) / `GCP_API_KEY` (fallback), `INFRACOST_API_KEY`, `PRICING_MAX_RECORDS`
- **Frontend:** `VITE_API_BASE_URL`, `VITE_ENABLE_AI_CHAT`
- **Processing:** `GEMINI_API_KEY`
- **Data Sourcing:** `COMMODITY_PRICE_API_KEY`

## Testing Notes

- Backend tests use a **separate database** (`hackeurope_test`) — not the dev DB
- Test fixtures use SAVEPOINT rollback for isolation (no data persists between tests)
- `conftest.py` imports `app.models` to register all models with `Base.metadata`
- `pytest.ini` sets `asyncio_mode = auto`

## Key Patterns

- **New model?** Add to `app/models/`, import in `app/models/__init__.py`, generate Alembic migration
- **New endpoint?** Router in `app/api/routers/`, register in `app/api/routers/__init__.py`, add repo+service+dependency
- **Pricing sync flow:** `POST /api/v1/pricing/sync` → fetcher (HTTP to AWS/Azure/GCP APIs) → normalizer → upsert to `cloud_pricing` → aggregate to `market_data`
- **Dummy API responses** live in `dummy/reponse_example/raw_*.json` with a `transform_to_db.py` transformer script

---

## Documentation rule
After any architecture change (new criteria, routing logic, schemas, pipeline steps, tool interfaces), always update:
- `CLAUDE.md` — keep fully up to date
- `processing_layer/README.md` — update sparsely/concisely only when relevant

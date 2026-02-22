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

| Criterion | Weight | Scope | Prompt key |
|---|---|---|---|
| `FORMAL_VALIDITY` | 20 pts | invoice-level | `JUDGE_FORMAL_VALIDITY` |
| `MARKET_PRICE_ALIGNED` | 27 pts | per line item | `JUDGE_MARKET_PRICE` |
| `HISTORICAL_PRICE_CONSISTENT` | 27 pts | per line item | `JUDGE_HISTORICAL_PRICE` |
| `COMPETITOR_PRICE_ALIGNED` | 26 pts | per line item | `JUDGE_COMPETITOR_PRICE` |

**Current state:**
- Extraction: fully implemented
- Backend `/api/v1/extraction/` now performs two Gemini calls: first-pass extraction, then second-pass risk review using vendor invoices + `cloud_pricing` context, persisting data to `vendors`/`invoices`/`items`.
- Rubric schemas + scoring + criteria + routing: implemented; `evaluate_criterion` now supports deterministic evaluation from extraction+signals context (competitor criterion remains unavailable without source data).
- Analysis + negotiation: scaffolded end-to-end
- `signals/compute.py`: stub — raises `NotImplementedError` pending tool return shapes
- `tools/` (`SqlDatabaseTool`, `MarketDataTool`): stubs — raise `NotImplementedError`

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

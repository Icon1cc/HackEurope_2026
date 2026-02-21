# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**InvoiceGuard** — B2B invoice anomaly detection platform. Ingests cloud vendor invoices, extracts data via LLM (Gemini), compares against real-time market pricing, and flags overcharges.

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

1. **Extraction** — Gemini reads invoice (PDF/image) → `InvoiceExtraction`
2. **Context** — fetches historical data + market prices (tool stubs)
3. **Signals** — deterministic Python math → `PriceSignal` objects (stub)
4. **LLM synthesis** — Gemini receives signal statements → `InvoiceAnalysis`
5. **Injection** — deterministic signals injected post-LLM (immutable)

Key: all LLM calls use `response_json_schema` + `model_validate_json`. Math stays in Python, reasoning stays in LLM. `LLMProvider` abstraction — Gemini wired up, swappable.

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

- **Backend:** `DATABASE_URL` (asyncpg connection string), `GCP_API_KEY`, `INFRACOST_API_KEY`, `PRICING_MAX_RECORDS`
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

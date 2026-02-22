# InvoiceGuard

Autonomous AI protection for accounts payable. InvoiceGuard ingests cloud vendor invoices (PDF/image), extracts structured data via Gemini, and runs a deterministic rubric scoring pipeline — comparing each line item against real-time market prices and historical vendor data. Suspicious invoices are flagged for human review or auto-escalated with a Gemini-drafted renegotiation email.

## Quick Start

```bash
# 1. Copy and fill env vars
cp backend/.env.example backend/.env   # add GEMINI_API_KEY, ANTHROPIC_API_KEY

# 2. Start Postgres + Backend
docker-compose up -d

# 3. Apply DB migrations & seed
cd backend && uv run alembic upgrade head && uv run python seed.py

# 4. Start frontend
cd frontend && npm install && npm run dev
```

| Service    | URL                          |
|------------|------------------------------|
| Frontend   | http://localhost:3000        |
| Backend API| http://localhost:8000        |
| API Docs   | http://localhost:8000/docs   |
| PostgreSQL | localhost:**5433** / `hackeurope` |

---

## Repo Structure

```
├── backend/          FastAPI + SQLAlchemy (async) — REST API & pipeline orchestration
├── frontend/         React 18 + TypeScript + Vite + Tailwind — web UI
├── processing_layer/ Pydantic schemas, signals, rubric scoring, LLM providers
├── data_sourcing/    Playwright scraper — AWS/Azure/GCP pricing → DB
├── docker-compose.yaml
└── Invoices_2026/    Sample invoice PDFs for testing
```

---

## Environment Variables

**`backend/.env`** (copy from `.env.example`):

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://postgres:postgres@localhost:5433/hackeurope` |
| `GEMINI_API_KEY` | ✅ | Invoice extraction (Gemini Flash) |
| `ANTHROPIC_API_KEY` | ✅ | Reasoning + negotiation (Claude Sonnet 4.6) |
| `REASONING_PROVIDER` | — | `claude` (default) or `gemini` |
| `PRICING_MAX_RECORDS` | — | Max cloud pricing rows to load (default: 5000) |

**`frontend/.env`** (copy from `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Backend URL |
| `VITE_API_VERSION` | `v1` | API version prefix |

---

## Pipeline

`POST /api/v1/extraction/` — upload a PDF or image invoice:

1. **Gemini extraction** → structured `InvoiceExtraction` (line items, totals, vendor)
2. **Signal computation** — deterministic Python: duplicate check, market price deviation, historical deviation, total drift, math consistency
3. **Rubric scoring** — 4 criteria, 0–100 confidence score (no LLM in scoring path)
4. **Claude analysis** — forensic summary + anomaly flags
5. **Routing** — `APPROVED` (≥80) / `HUMAN_REVIEW` (40–79) / `ESCALATE_NEGOTIATION` (<40)
6. **Negotiation draft** — Claude drafts renegotiation email if escalated

---

## Development

### Backend
```bash
cd backend
uv sync
uv run alembic upgrade head          # apply migrations
uv run python seed.py                # seed sample data (drops & recreates)
uv run uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # dev server → port 3000
npm run type-check   # TypeScript check
npm run build        # production build
```

### Processing Layer
```bash
cd processing_layer
uv sync
uv run python tests/test_invoice_extraction.py <invoice.pdf>
```

### Data Sourcing (cloud pricing)
```bash
cd data_sourcing
uv sync
uv run python -m clients.cloud_pricing_scraper --out data/cloud_pricing.json
# Then POST /api/v1/pricing/sync to load into DB
```

### Tests
```bash
cd backend
pytest                          # requires hackeurope_test DB on port 5433
pytest tests/test_pricing.py   # single file
```

---

## Tech Stack

| Component | Stack |
|-----------|-------|
| Backend | FastAPI, SQLAlchemy (async), PostgreSQL 15, Alembic, asyncpg |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Radix UI |
| LLM – Extraction | Google Gemini (structured JSON schema output) |
| LLM – Reasoning | Anthropic Claude Sonnet 4.6 |
| Pricing data | AWS / Azure / GCP scraped via Playwright |
| Infra | Docker Compose (Postgres + Backend) |

---

## Design Choices

### Rationale behind Confidence Scoring

InvoiceGuard assigns a confidence score to each processed invoice, reflecting the system's certainty in its assessment. This score is derived from explicit, human-readable criteria. We are following latest research in the LLM evaluation space: A rubric in LLM-as-a-judge evaluation is a structured scoring guide with predefined criteria, dimensions (e.g., correctness, coherence), and score levels that directs the judge LLM to assess generated outputs consistently and transparently. It replaces vague pointwise scoring by defining what "good" looks like across categories, enabling calibrated, multidimensional judgments that align with human preferences. For more details, see:

- [LLM-Rubric: A Multidimensional, Calibrated Approach to Automated Evaluation of Natural Language Texts](https://arxiv.org/abs/2501.00274)
- [Rubrics as Rewards: Reinforcement Learning Beyond Verifiable Domains](https://arxiv.org/abs/2507.17746)

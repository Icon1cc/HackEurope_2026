<div align="center">
  <img src="logo.svg" alt="FairPay Agent Logo" width="200"/>

  # FairPay Agent

  **Autonomous AI protection for accounts payable**

  B2B invoice anomaly detection — upload a cloud vendor invoice, get a trust score, anomaly flags, and an auto-drafted renegotiation email in seconds.
</div>

---

## What it does

FairPay Agent ingests cloud vendor invoices (PDF or image), extracts structured data via Gemini, benchmarks every line item against real-time AWS/Azure/GCP market prices and the vendor's own billing history, then routes the invoice through a deterministic rubric-based confidence score to one of three outcomes:

| Decision | Score | Action |
|---|---|---|
| `APPROVED` | ≥ 90 | Auto-approved, Stripe payment triggered |
| `HUMAN_REVIEW` | 40–79 | Flagged for analyst review in the UI |
| `ESCALATE_NEGOTIATION` | < 40 | Claude drafts a renegotiation email automatically |

---

## Pipeline — 5 Stages

### Stage 1 — Ingestion & Extraction

> Client uploads a PDF/image → triggers the Invoice Agent → **Gemini API (call #1)** extracts Invoice ID, date, line items, amounts and stores them in the database.

![Stage 1](<Stage 1.png>)

---

### Stage 2 — Context Gathering

> **Claude API (call #2)** fetches vendor history from the DB and triggers a real-time pricing API request — both signals are retrieved and stored for the reasoning step.

![Stage 2](<Stage 2.png>)

---

### Stage 3 — Reasoning & Rubric Scoring

> **Claude Reasoning** compares real-time market data against the invoice, checks for duplicates, inconsistencies, and overpricing against historical data, then computes a **trust score** via a multi-criteria rubric (LLM-as-a-judge approach).

![Stage 3](<Stage 3.png>)

---

### Stage 4 — Routing & Payment

> The system decides between auto-approval and human escalation. If approved, a **Stripe** request is fired with the invoice ID; the Stripe webhook confirms payment and marks the vendor as paid. If suspicious, the client can approve, reject, or send a Claude-drafted negotiation email.

![Stage 4](<Stage 4.png>)

---

### Stage 5 — AI Usage & Savings Tracking (Paid.ai)

> A **Paid AI Wrapper** fetches all agent statistics and displays per-invoice AI usage costs and estimated savings — giving full observability over the autonomous pipeline.

![Stage 5](<Stage 5.png>)

---

## Rubric Scoring (0–100)

No LLM in the scoring path — fully deterministic:

| Criterion | Weight | Signal |
|---|---|---|
| Formal Validity | 20 pts | Duplicate check + required field presence |
| Market Price Alignment | 27 pts | Per-line deviation vs. AWS/Azure/GCP prices |
| Historical Price Consistency | 27 pts | Per-line deviation vs. past vendor invoices |
| Vendor Total Drift | 26 pts | Invoice-level drift vs. vendor history |

Criteria with no available data are excluded from the denominator — the score scales to available evidence.

---

## Data Usage & Collection

FairPay Agent continuously tracks real-time pricing data from six external sources. Each source is polled by the `data_sourcing/` scraper, its raw JSON response is normalised into a unified schema, and the cleaned records are upserted into the `cloud_pricing` table — the ground truth the rubric uses for market benchmarking.

| Source | Data collected | Used for |
|---|---|---|
| **AWS (S3, CloudFront, RDS/EC)** | Per-SKU unit prices, region, instance type, storage tier | Line-item market deviation signal |
| **Azure** | VM sizes, managed disk, bandwidth pricing by region | Line-item market deviation signal |
| **GCP** | Compute Engine, Cloud Storage, egress pricing | Line-item market deviation signal |
| **Infracost** | Infrastructure cost estimates mapped to cloud resources | Cross-validation of unit prices; enriches SKU matching |

### Collection pipeline

```
External API / scraper
        │
        ▼
 Raw JSON response          ← provider-specific schema (AWS Pricing API,
        │                      Azure Retail Prices API, GCP Cloud Billing
        ▼                      Catalog, Infracost API)
 Normaliser / cleaner       ← strips nulls, unifies field names, converts
        │                      units (e.g. per-hour ↔ per-month), deduplicates
        ▼                      on (provider, region, sku_description)
 cloud_pricing table        ← single unified catalogue, upsert-on-conflict
        │
        ▼
 Signals engine             ← compute_signals() queries cloud_pricing,
        │                      matches each invoice line item by keyword,
        ▼                      computes % deviation from market price
 Rubric (MARKET_PRICE_ALIGNED criterion, 27 pts)
```

### What "cleaning" means in practice

Raw provider responses are heterogeneous — AWS returns a nested `terms` → `priceDimensions` tree, Azure returns a flat list with `retailPrice` / `unitPrice` split, GCP uses a `tieredRates` array, and Infracost uses its own resource-mapped schema. The normaliser:

1. **Flattens** nested price dimensions into a single `unit_price` float
2. **Standardises units** — all prices stored as per-unit-per-hour where applicable
3. **Strips non-purchasable entries** (reserved instances, spot tiers) that would skew comparisons
4. **Deduplicates** on `(provider, region, sku_description)` with `ON CONFLICT DO UPDATE` so re-runs never create phantom duplicates
5. **Produces a `sku_description` string** used by the signal engine for fuzzy keyword matching against invoice line-item descriptions

The result is a clean, provider-agnostic catalogue that the rubric can query without any provider-specific logic leaking into the scoring path.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI · SQLAlchemy (async) · PostgreSQL 15 · Alembic |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · Radix UI |
| LLM — Extraction | Google Gemini (structured JSON schema output) |
| LLM — Reasoning & Negotiation | Anthropic Claude Sonnet 4.6 |
| Pricing data | AWS / Azure / GCP APIs + Playwright scraper |
| Payments | Stripe (webhooks) |
| AI Observability | Paid.ai wrapper |
| Infra | Docker Compose |

---

## Quick Start

```bash
# 1. Copy env files and add API keys
cp backend/.env.example backend/.env    # GEMINI_API_KEY, ANTHROPIC_API_KEY, STRIPE_*

# 2. Start Postgres + Backend
docker-compose up -d

# 3. Apply DB migrations & seed sample data
cd backend && uv run alembic upgrade head && uv run python seed.py

# 4. Start frontend
cd frontend && npm install && npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5433 / `hackeurope` |

---

## Repository Structure

```
├── backend/           FastAPI + SQLAlchemy — REST API & pipeline orchestration
├── frontend/          React 18 + TypeScript — web UI
├── processing_layer/  Pydantic schemas, signals, rubric scoring, LLM providers
├── data_sourcing/     AWS/Azure/GCP pricing scraper
└── docker-compose.yaml
```

---

## Key Design Choices

- **No LLM in the scoring path** — signals are pure Python math; Claude does reasoning, not arithmetic.
- **Rubric-as-a-judge** — inspired by [LLM-Rubric (arXiv:2501.00274)](https://arxiv.org/abs/2501.00274): structured, multi-dimensional criteria replace opaque pointwise scores.
- **Dual-provider LLM** — Gemini for multimodal document extraction; Claude Sonnet 4.6 for forensic reasoning and negotiation drafting.
- **Fail-fast pipeline** — assert preconditions at every step; no silent defaults.
- **Stripe-native payment flow** — approved invoices trigger payment automatically; webhooks close the loop without manual intervention.

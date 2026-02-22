# InvoiceGuard — processing_layer

LLM-powered invoice anomaly detection with rubric-based confidence scoring.

## Quickstart

```bash
cd processing_layer
pip install -e .          # or: uv sync
cp ../.env.example ../.env
pytest tests/
```

Required env var: `GEMINI_API_KEY` (preferred). `GCP_API_KEY` is also accepted as a fallback.

---

## Design: Rubric-Based Confidence Score

Each invoice gets a `confidence_score` (0–100) built from explicit per-criterion verdicts — not an unconstrained LLM number. Every point has a criterion, a yes/no verdict, and a 1-sentence rationale (fully auditable).

```
score = sum(points_awarded for available criteria)
        / sum(max_points   for available criteria)  × 100
```
Criteria with no data (tool stub) are excluded from the denominator.

> Follows recent research: [arxiv 2507.17746](https://arxiv.org/abs/2507.17746) · [arxiv 2501.00274](https://arxiv.org/abs/2501.00274)

---

## Pipeline (step by step)

```
Invoice document (PDF / image)
        │
        ▼
1. EXTRACTION  ──────────────────────────────────────────────────────────
   Gemini reads document, returns typed fields (vendor, line items, totals…)
   In:  bytes (raw document)
   Out: schemas/invoice.py → InvoiceExtraction, LineItem
   Key: extraction/invoice.py:InvoiceExtractor
        prompts.py:INVOICE_EXTRACTION_PROMPT
        llm/gemini.py:GeminiProvider

        │
        ▼
2. CONTEXT GATHERING  ───────────────────────────────────────────────────
   Fetches historical invoices (SQL) + real-time market prices
   In:  InvoiceExtraction
   Out: dict → keys: "invoice_history", "market_prices"
   Key: analysis/invoice.py:InvoiceAnalyzer._gather_context()
        tools/sql_db.py:SqlDatabaseTool.fetch_invoice_history()   ← stub
        tools/market_data.py:MarketDataTool.get_spot_price()      ← stub

        │
        ▼
3. SIGNAL COMPUTATION  ──────────────────────────────────────────────────
   Deterministic Python math on context → human-readable price signals
   In:  InvoiceExtraction + dict (context)
   Out: schemas/signals.py → list[PriceSignal]  (statement, is_anomalous, SignalType, SignalScope)
   Key: signals/compute.py:compute_signals()   ← stub (backend computes signals inline)
        schemas/signals.py
        constants.py:PRICE_TOLERANCE_PCT

        │
        ▼
4. RUBRIC EVALUATION  ───────────────────────────────────────────────────
   Per-criterion judge calls → deterministic score aggregation
   In:  InvoiceExtraction + dict (context)
   Out: schemas/rubric.py → InvoiceRubric (list[CriterionResult] + total_score 0–100)
   Key: rubric/criteria.py:CRITERIA
        rubric/evaluator.py:evaluate_criterion()   ← deterministic signal-based implementation
        rubric/scoring.py:aggregate_score()
        prompts.py:JUDGE_FORMAL_VALIDITY / JUDGE_MARKET_PRICE / JUDGE_HISTORICAL_PRICE / JUDGE_COMPETITOR_PRICE
        constants.py:PRICE_TOLERANCE_PCT

   Criteria (weights sum to 100, enforced at import):
     FORMAL_VALIDITY             20 pts  — invoice-level: required fields, dates, no duplicate ID
     MARKET_PRICE_ALIGNED        27 pts  — vs real-time market spot       (per line item)
     HISTORICAL_PRICE_CONSISTENT 27 pts  — vs past vendor invoices        (per line item)
     COMPETITOR_PRICE_ALIGNED    26 pts  — vs similar vendors in DB       (per line item)

        │
        ▼
5. LLM SYNTHESIS  ───────────────────────────────────────────────────────
   Gemini reasons over signals + rubric score → anomaly report
   In:  InvoiceExtraction + list[PriceSignal] + InvoiceRubric
   Out: schemas/analysis.py → InvoiceAnalysis (anomaly_flags, line_item_analyses, is_duplicate, summary)
   Key: analysis/invoice.py:InvoiceAnalyzer._build_prompt() / _run_pipeline()
        prompts.py:INVOICE_ANALYSIS_PROMPT
   Note: signals injected post-generation — LLM cannot overwrite them

        │
        ▼
6. ROUTING  ─────────────────────────────────────────────────────────────
   Pure Python three-tier decision — no LLM
   In:  InvoiceAnalysis + int (confidence_score) + InvoiceRubric
   Out: schemas/result.py → InvoiceDecision (action: InvoiceAction, reason)
   Key: routing/decision.py:decide()
        constants.py:APPROVAL_THRESHOLD=80, ESCALATION_THRESHOLD=40

   score ≥ 80                 →  APPROVED
   40 ≤ score < 80            →  HUMAN_REVIEW
   score < 40                 →  ESCALATE_NEGOTIATION
   FORMAL_VALIDITY failed     →  HUMAN_REVIEW  (overrides score, always)
   is_duplicate=True          →  ESCALATE_NEGOTIATION  (overrides score)

        │
        ▼
7. NEGOTIATION (conditional)  ───────────────────────────────────────────
   Only runs if action == ESCALATE_NEGOTIATION
   In:  InvoiceAnalysis
   Out: schemas/result.py → NegotiationDraft (subject, body, key_points)
   Key: negotiation/agent.py:NegotiationAgent.draft_email()
        prompts.py:NEGOTIATION_PROMPT

        │
        ▼
8. RESULT  ──────────────────────────────────────────────────────────────
   Out: schemas/result.py → InvoiceResult
     .analysis          InvoiceAnalysis
     .rubric            InvoiceRubric
     .decision          InvoiceDecision
     .confidence_score  int  (computed field = rubric.total_score)
     .negotiation_draft NegotiationDraft | None
```

---

## File Layout

```
processing_layer/
    extraction/         invoice extractor (Gemini image/PDF)
    analysis/           InvoiceAnalyzer: orchestrates full pipeline
    signals/            PriceSignal computation (stub)
    rubric/
        criteria.py     CRITERIA list + weight-sum assertion
        evaluator.py    evaluate_criterion() — deterministic signal-based evaluation
        scoring.py      aggregate_score()   — deterministic math
    routing/            decide() — three-tier routing + formal override
    negotiation/        NegotiationAgent — renegotiation email draft
    schemas/
        invoice.py      InvoiceExtraction, LineItem
        analysis.py     InvoiceAnalysis, AnomalyFlag, …
        rubric.py       CriterionId, CriterionVerdict, CriterionResult, InvoiceRubric
        result.py       InvoiceResult, InvoiceDecision, InvoiceAction
    llm/                LLMProvider base + GeminiProvider
    tools/              SqlDatabaseTool, MarketDataTool (stubs)
    prompts.py          All LLM prompts (extraction, analysis, judge × 4, negotiation)
    constants.py        APPROVAL_THRESHOLD=80, ESCALATION_THRESHOLD=40, PRICE_TOLERANCE_PCT=15
```

---

## Backend Integration Status

This module lives at `backend/processing_layer/`. The backend extraction endpoint (`POST /api/v1/extraction/`) **does NOT use `InvoiceAnalyzer`** as orchestrator — it has its own inline pipeline.

| Component | Status in backend |
|---|---|
| `extraction/invoice.py:InvoiceExtractor` | ✅ Used — Gemini call #1 |
| `rubric/evaluator.py:evaluate_rubric()` | ✅ Used — signals-based, fully implemented |
| `routing/decision.py:decide()` | ✅ Used |
| `llm/gemini.py:GeminiProvider` | ✅ Used — both LLM calls |
| `schemas/*` | ✅ Used |
| `analysis/invoice.py:InvoiceAnalyzer` | ❌ Bypassed — backend has own pipeline |
| `signals/compute.py:compute_signals()` | ❌ Bypassed — backend computes signals inline |
| `tools/SqlDatabaseTool` | ❌ Unused — backend uses SQLAlchemy repos |
| `tools/MarketDataTool` | ❌ Unused |
| `negotiation/agent.py:NegotiationAgent` | ⚠️ Implemented, not yet wired to any endpoint |

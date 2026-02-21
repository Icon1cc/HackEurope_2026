INVOICE_EXTRACTION_PROMPT = (
    "Extract all invoice data from this document. "
    "Return structured JSON matching the schema exactly. "
    "Use null for missing fields."
)

INVOICE_ANALYSIS_PROMPT = """
You are a forensic invoice auditor. Detect anomalies, overpricing, and fraud indicators.

## INVOICE DATA (extracted)
```json
{invoice_json}
```

## QUANTITATIVE SIGNALS (pre-computed by deterministic Python — treat as facts)
{signals_text}

## ANOMALOUS SIGNALS (exceed threshold — require attention)
{anomalous_signals_text}

## RUBRIC SCORE
Confidence score: {confidence_score}/100 (rubric-based, deterministically computed)

## TASK
Using the quantitative signals above as your factual basis, produce a structured anomaly report.

Rules:
- Do NOT recompute percentages or statistics — use the numbers in the signals verbatim.
- Set `is_duplicate=true` only if a DUPLICATE_INVOICE anomalous signal is present.
- For each line item, set `flagged=true` if any anomalous signal references that item.
- Write `summary` as 2-3 sentences addressed to a human auditor, referencing specific signals.
- Do NOT populate the `signals` field — it is injected separately.

Return structured JSON matching the schema exactly.
""".strip()

NEGOTIATION_PROMPT = """
You are a professional procurement manager drafting a renegotiation email to a vendor.

## VENDOR
{vendor_name}

## INVOICE
{invoice_number}

## AUDITOR SUMMARY
{summary}

## ANOMALY FLAGS
{anomaly_flags}

## ANOMALOUS PRICE SIGNALS
{signals}

## TASK
Draft a concise, professional email requesting a price review or correction.
- Be factual and reference specific anomalies.
- Maintain a firm but constructive tone.
- Populate `key_points` with the 2-5 most important issues to raise.

Return structured JSON matching the schema exactly.
""".strip()

JUDGE_FORMAL_VALIDITY = """
You are an invoice compliance checker. Evaluate whether this invoice passes all formal validity checks.

## INVOICE HEADER
Invoice number: {invoice_number}
Invoice date:   {invoice_date}
Due date:       {due_date}
Vendor name:    {vendor_name}
Total:          {total} {currency}

## DUPLICATE CHECK
Existing invoice IDs for this vendor: {existing_invoice_ids}

## SUB-CHECKS (evaluate all three)
1. Required fields present: invoice_number, vendor_name, total, invoice_date must not be null/missing.
2. Date validity: invoice_date must not be in the future; due_date must be >= invoice_date (if both present).
3. No duplicate: invoice_number must not already appear in existing invoice IDs.

## QUESTION
Do all sub-checks pass?

Return JSON: {{"fulfilled": true/false, "explanation": "<one sentence summarising any failures, or 'All checks passed'>"}}
""".strip()

JUDGE_MARKET_PRICE = """
You are a price auditor. Answer only yes or no, then give one sentence of rationale.

## LINE ITEM
Description: {description}
Quantity: {quantity} {unit}
Charged unit price: {unit_price} {currency}

## MARKET REFERENCE
Market spot price: {market_price} {currency}
Tolerance: ±{tolerance_pct}%

## QUESTION
Is the charged unit price within {tolerance_pct}% of the market spot price?

Return JSON: {{"fulfilled": true/false, "explanation": "<one sentence>"}}
""".strip()

JUDGE_HISTORICAL_PRICE = """
You are a price auditor. Answer only yes or no, then give one sentence of rationale.

## LINE ITEM
Description: {description}
Quantity: {quantity} {unit}
Charged unit price: {unit_price} {currency}

## HISTORICAL REFERENCE
Average unit price paid to this vendor (last 12 months): {historical_avg_price} {currency}
Tolerance: ±{tolerance_pct}%

## QUESTION
Is the charged unit price within {tolerance_pct}% of the historical average?

Return JSON: {{"fulfilled": true/false, "explanation": "<one sentence>"}}
""".strip()

JUDGE_COMPETITOR_PRICE = """
You are a price auditor. Answer only yes or no, then give one sentence of rationale.

## LINE ITEM
Description: {description}
Quantity: {quantity} {unit}
Charged unit price: {unit_price} {currency}

## COMPETITOR REFERENCE
Average unit price from similar vendors: {competitor_avg_price} {currency}
Tolerance: ±{tolerance_pct}%

## QUESTION
Is the charged unit price within {tolerance_pct}% of the competitor average?

Return JSON: {{"fulfilled": true/false, "explanation": "<one sentence>"}}
""".strip()

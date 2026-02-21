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

## TASK
Using the quantitative signals above as your factual basis, produce a structured anomaly report.

Rules:
- Do NOT recompute percentages or statistics — use the numbers in the signals verbatim.
- Set `is_duplicate=true` only if a DUPLICATE_INVOICE anomalous signal is present.
- For each line item, set `flagged=true` if any anomalous signal references that item.
- Set `confidence_score` 0–100: 100 = business as usual / completely clean, 0 = highly suspicious.
- If no signals are available, set `confidence_score=50` and note uncertainty in `summary`.
- Write `summary` as 2-3 sentences addressed to a human auditor, referencing specific signals.
- Do NOT populate the `signals` field — it is injected separately.

Return structured JSON matching the schema exactly.
""".strip()

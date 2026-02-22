# HackEurope_2026



### LLM Architecture

InvoiceGuard uses a **dual-provider** LLM setup to separate extraction from reasoning:

| Role | Provider | Model | Used for |
|---|---|---|---|
| Extraction | Google Gemini | `gemini-2.0-flash` | PDF/image → structured `InvoiceExtraction` (uses Gemini File API) |
| Reasoning | Anthropic Claude | `claude-sonnet-4-6` | Anomaly analysis → `InvoiceAnalysis` + negotiation email → `NegotiationDraft` |

**Required env vars (backend `.env`):**
```
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
```

`REASONING_PROVIDER=claude` is the default and can be overridden to `gemini` for fallback.

---

### Design Choices

**Rationale behind Confidence Scoring.** InvoiceGuard assigns a confidence score to each processed invoice, reflecting the system's certainty in its assessment. This score is derived from explicit, human-readable criteria. We are following latest research in the LLM evaluation space: 
A rubric in LLM-as-a-judge evaluation is a structured scoring guide with predefined criteria, dimensions (e.g., correctness, coherence), and score levels that directs the judge LLM to assess generated outputs consistently and transparently. It replaces vague pointwise scoring by defining what "good" looks like across categories, enabling calibrated, multidimensional judgments that align with human preferences. For more details, see:
- [LLM-Rubric: A Multidimensional, Calibrated Approach to Automated Evaluation of Natural Language Texts](https://arxiv.org/abs/2501.00274)
- [Rubrics as Rewards: Reinforcement Learning Beyond Verifiable Domains](https://arxiv.org/abs/2507.17746)

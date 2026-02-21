# HackEurope_2026



### Design Choices

**Rationale behind Confidence Scoring.** InvoiceGuard assigns a confidence score to each processed invoice, reflecting the system's certainty in its assessment. This score is derived from explicit, human-readable criteria. We are following latest research in the LLM evaluation space: 
A rubric in LLM-as-a-judge evaluation is a structured scoring guide with predefined criteria, dimensions (e.g., correctness, coherence), and score levels that directs the judge LLM to assess generated outputs consistently and transparently. It replaces vague pointwise scoring by defining what "good" looks like across categories, enabling calibrated, multidimensional judgments that align with human preferences. For more details, see:
- [LLM-Rubric: A Multidimensional, Calibrated Approach to Automated Evaluation of Natural Language Texts](https://arxiv.org/abs/2501.00274)
- [Rubrics as Rewards: Reinforcement Learning Beyond Verifiable Domains](https://arxiv.org/abs/2507.17746)

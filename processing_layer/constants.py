PRICE_TOLERANCE_PCT = 15.0   # within this % of reference price = aligned

APPROVAL_THRESHOLD = 80      # score >= this → APPROVED
ESCALATION_THRESHOLD = 40    # score < this → ESCALATE_NEGOTIATION; between → HUMAN_REVIEW

DEFAULT_MODEL = "gemini-3-flash-preview"         # main LLM provider model
DEFAULT_GRADER_MODEL = "gemini-3-flash-preview"  # grader/judge model (can differ from main)

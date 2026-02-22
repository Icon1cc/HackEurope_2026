"""Paid.ai value attribution – tracks financial impact of the AI agent."""

import logging
from typing import Any

from paid import AsyncPaid, Signal, CustomerByExternalId, ProductByExternalId

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncPaid | None = None

AGENT_PRODUCT_ID = "invoice_guard_001"


def init_paid() -> None:
    """Initialise the Paid.ai async client (called once at startup)."""
    global _client
    settings = get_settings()
    if not settings.paid_api_key:
        logger.warning("PAID_API_KEY not set – Paid.ai tracking disabled")
        return
    _client = AsyncPaid(token=settings.paid_api_key)
    logger.info("Paid.ai client initialised")


async def track_value(
    vendor_id: str,
    event_name: str,
    value: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Fire a single value-metric signal to Paid.ai.

    Silently no-ops when the client is not configured so the pipeline
    never breaks because of attribution tracking.
    """
    if _client is None:
        return
    try:
        signal = Signal(
            event_name=event_name,
            customer=CustomerByExternalId(external_customer_id=vendor_id),
            attribution=ProductByExternalId(external_product_id=AGENT_PRODUCT_ID),
            data={"value_generated": value, **(metadata or {})},
        )
        await _client.signals.create_signals(signals=[signal])
        logger.info("Paid.ai signal sent: %s  value=%.2f  vendor=%s", event_name, value, vendor_id)
    except Exception as exc:
        logger.warning("Paid.ai tracking failed for %s: %s", event_name, exc)

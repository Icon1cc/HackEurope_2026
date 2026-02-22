import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select, update

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.payment import Payment
from app.models.invoice import Invoice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    settings = get_settings()
    if not settings.stripe_webhook_secret:
        logger.warning("STRIPE_WEBHOOK_SECRET not configured, skipping signature verification")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data_object = event["data"]["object"]

    logger.info("Received Stripe webhook: %s", event_type)

    if event_type == "transfer.paid":
        await _handle_transfer_paid(data_object)
    elif event_type == "checkout.session.completed":
        await _handle_subscription_created(data_object)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_cancelled(data_object)

    return {"status": "ok"}


async def _handle_transfer_paid(transfer: dict) -> None:
    invoice_id = transfer.get("metadata", {}).get("invoice_id")
    transfer_id = transfer.get("id")

    if not invoice_id:
        logger.warning("transfer.paid event missing invoice_id in metadata")
        return

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Payment)
            .where(Payment.stripe_payout_id == transfer_id)
            .values(status="confirmed", confirmed_at=datetime.now(timezone.utc))
        )
        await db.execute(
            update(Invoice)
            .where(Invoice.id == invoice_id)
            .values(status="paid", updated_at=datetime.now(timezone.utc))
        )
        await db.commit()

    logger.info("Transfer %s confirmed, invoice %s marked as paid", transfer_id, invoice_id)


async def _handle_subscription_created(session: dict) -> None:
    user_id = session.get("metadata", {}).get("user_id")
    customer_id = session.get("customer")
    logger.info("Subscription created for user %s (customer %s)", user_id, customer_id)


async def _handle_subscription_cancelled(subscription: dict) -> None:
    customer_id = subscription.get("customer")
    logger.info("Subscription cancelled for customer %s", customer_id)

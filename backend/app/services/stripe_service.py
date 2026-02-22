import logging
from uuid import UUID, uuid4

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor import Vendor
from app.models.payment import Payment

logger = logging.getLogger(__name__)


def _generate_internal_transfer_id() -> str:
    return f"local_tr_{uuid4().hex}"


async def execute_vendor_payment(
    invoice_id: UUID,
    vendor_id: UUID,
    amount_euros: float,
    db: AsyncSession,
) -> dict:
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()

    if not vendor:
        logger.error("Vendor %s not found for invoice %s", vendor_id, invoice_id)
        return {"error": "Vendor not found"}

    amount_cents = int(amount_euros * 100)
    transfer_id = _generate_internal_transfer_id()

    if vendor.stripe_account_id and stripe.api_key:
        try:
            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency="eur",
                destination=vendor.stripe_account_id,
                metadata={
                    "invoice_id": str(invoice_id),
                    "vendor_id": str(vendor_id),
                },
            )
            stripe_transfer_id = getattr(transfer, "id", None)
            if stripe_transfer_id:
                transfer_id = stripe_transfer_id
                logger.info("Stripe transfer %s created for invoice %s", transfer_id, invoice_id)
            else:
                logger.warning(
                    "Stripe transfer returned no id for invoice %s, using internal transfer id %s",
                    invoice_id,
                    transfer_id,
                )
        except stripe.StripeError as exc:
            logger.error(
                "Stripe transfer failed for invoice %s: %s. Using internal transfer id %s",
                invoice_id,
                exc,
                transfer_id,
            )
    else:
        logger.info(
            "Skipping Stripe transfer for invoice %s (vendor %s has no stripe_account_id or no API key). "
            "Using internal transfer id %s",
            invoice_id,
            vendor_id,
            transfer_id,
        )

    payment = Payment(
        invoice_id=invoice_id,
        stripe_payout_id=transfer_id,
        amount=amount_euros,
        currency="eur",
        status="initiated",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return {"payment_id": str(payment.id), "transfer_id": transfer_id, "status": "initiated"}

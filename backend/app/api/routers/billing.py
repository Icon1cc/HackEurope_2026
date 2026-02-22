import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"], dependencies=[Depends(get_current_user)])


class CheckoutRequest(BaseModel):
    user_id: str
    user_email: str


@router.post("/create-checkout-session")
async def create_checkout_session(body: CheckoutRequest):
    settings = get_settings()
    if not settings.stripe_pro_price_id:
        raise HTTPException(status_code=500, detail="Stripe Pro price ID not configured")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=body.user_email,
            line_items=[{"price": settings.stripe_pro_price_id, "quantity": 1}],
            metadata={"user_id": body.user_id},
            success_url="http://localhost:3000/dashboard?upgrade=success",
            cancel_url="http://localhost:3000/dashboard?upgrade=cancelled",
        )
        return {"checkout_url": session.url}
    except stripe.StripeError as exc:
        logger.error("Failed to create checkout session: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

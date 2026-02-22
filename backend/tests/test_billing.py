"""Endpoint tests for POST /api/v1/billing/create-checkout-session."""

from unittest.mock import patch, MagicMock

import stripe as stripe_lib

BASE = "/api/v1/billing/create-checkout-session"

VALID_BODY = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "user_email": "test@example.com",
}


class TestBillingCheckout:
    @patch("app.api.routers.billing.stripe.checkout.Session.create")
    async def test_create_checkout_session(self, mock_create, client):
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/c/pay/cs_test_abc123"
        mock_create.return_value = mock_session

        resp = await client.post(BASE, json=VALID_BODY)
        assert resp.status_code == 200
        assert resp.json()["checkout_url"] == "https://checkout.stripe.com/c/pay/cs_test_abc123"

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["mode"] == "subscription"
        assert call_kwargs["customer_email"] == "test@example.com"

    @patch("app.api.routers.billing.stripe.checkout.Session.create")
    async def test_stripe_error(self, mock_create, client):
        mock_create.side_effect = stripe_lib.StripeError("Invalid API key")

        resp = await client.post(BASE, json=VALID_BODY)
        assert resp.status_code == 500
        assert "Invalid API key" in resp.json()["detail"]

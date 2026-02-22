"""Endpoint tests for POST /api/v1/webhooks/stripe."""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

import stripe as stripe_lib

from app.models.invoice import Invoice
from app.models.payment import Payment

BASE = "/api/v1/webhooks/stripe"


def _make_settings(*, webhook_secret="whsec_test"):
    s = MagicMock()
    s.stripe_webhook_secret = webhook_secret
    return s


def _make_event(event_type, data_object):
    return {
        "type": event_type,
        "data": {"object": data_object},
    }


class TestStripeWebhook:
    @patch("app.api.routers.webhooks.get_settings", return_value=_make_settings(webhook_secret=""))
    async def test_missing_webhook_secret(self, mock_settings, client):
        resp = await client.post(
            BASE,
            content=b'{}',
            headers={"stripe-signature": "t=123,v1=sig"},
        )
        assert resp.status_code == 500
        assert "Webhook secret not configured" in resp.json()["detail"]

    @patch("app.api.routers.webhooks.get_settings", return_value=_make_settings())
    @patch("app.api.routers.webhooks.stripe.Webhook.construct_event")
    async def test_invalid_signature(self, mock_construct, mock_settings, client):
        mock_construct.side_effect = stripe_lib.SignatureVerificationError("bad sig", "sig_header")

        resp = await client.post(
            BASE,
            content=b'{}',
            headers={"stripe-signature": "t=123,v1=badsig"},
        )
        assert resp.status_code == 400
        assert "Invalid signature" in resp.json()["detail"]

    @patch("app.api.routers.webhooks.get_settings", return_value=_make_settings())
    @patch("app.api.routers.webhooks.stripe.Webhook.construct_event")
    @patch("app.api.routers.webhooks.AsyncSessionLocal")
    async def test_transfer_paid(self, mock_session_local, mock_construct, mock_settings, client, db_session):
        # Create invoice and payment in test DB
        invoice = Invoice(total=100.00, status="approved")
        db_session.add(invoice)
        await db_session.flush()

        payment = Payment(
            invoice_id=invoice.id,
            stripe_payout_id="tr_test_paid",
            amount=100.00,
            currency="eur",
            status="initiated",
        )
        db_session.add(payment)
        await db_session.flush()

        # Mock construct_event to return a transfer.paid event
        mock_construct.return_value = _make_event("transfer.paid", {
            "id": "tr_test_paid",
            "metadata": {"invoice_id": str(invoice.id)},
        })

        # Mock AsyncSessionLocal to use our test db_session
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=db_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session_local.return_value = mock_ctx

        resp = await client.post(
            BASE,
            content=b'{"type": "transfer.paid"}',
            headers={"stripe-signature": "t=123,v1=valid"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # Verify DB updates
        await db_session.refresh(payment)
        await db_session.refresh(invoice)
        assert payment.status == "confirmed"
        assert payment.confirmed_at is not None
        assert invoice.status == "paid"

    @patch("app.api.routers.webhooks.get_settings", return_value=_make_settings())
    @patch("app.api.routers.webhooks.stripe.Webhook.construct_event")
    @patch("app.api.routers.webhooks.AsyncSessionLocal")
    async def test_transfer_paid_no_metadata(self, mock_session_local, mock_construct, mock_settings, client):
        mock_construct.return_value = _make_event("transfer.paid", {
            "id": "tr_no_meta",
            "metadata": {},
        })

        resp = await client.post(
            BASE,
            content=b'{"type": "transfer.paid"}',
            headers={"stripe-signature": "t=123,v1=valid"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @patch("app.api.routers.webhooks.get_settings", return_value=_make_settings())
    @patch("app.api.routers.webhooks.stripe.Webhook.construct_event")
    async def test_checkout_completed(self, mock_construct, mock_settings, client):
        mock_construct.return_value = _make_event("checkout.session.completed", {
            "customer": "cus_test",
            "metadata": {"user_id": "usr_123"},
        })

        resp = await client.post(
            BASE,
            content=b'{"type": "checkout.session.completed"}',
            headers={"stripe-signature": "t=123,v1=valid"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @patch("app.api.routers.webhooks.get_settings", return_value=_make_settings())
    @patch("app.api.routers.webhooks.stripe.Webhook.construct_event")
    async def test_subscription_cancelled(self, mock_construct, mock_settings, client):
        mock_construct.return_value = _make_event("customer.subscription.deleted", {
            "customer": "cus_test",
        })

        resp = await client.post(
            BASE,
            content=b'{"type": "customer.subscription.deleted"}',
            headers={"stripe-signature": "t=123,v1=valid"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

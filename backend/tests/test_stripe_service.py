"""Unit tests for app.services.stripe_service.execute_vendor_payment."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import stripe as stripe_lib
from sqlalchemy import select

from app.models.vendor import Vendor
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.services.stripe_service import execute_vendor_payment

VENDORS = "/api/v1/vendors"
INVOICES = "/api/v1/invoices"


class TestExecuteVendorPayment:
    async def _create_vendor(self, db_session, *, stripe_account_id=None):
        vendor = Vendor(
            name="Test Vendor",
            category="computing",
            stripe_account_id=stripe_account_id,
        )
        db_session.add(vendor)
        await db_session.flush()
        return vendor

    async def _create_invoice(self, db_session, vendor_id):
        invoice = Invoice(vendor_id=vendor_id, total=250.00, status="approved")
        db_session.add(invoice)
        await db_session.flush()
        return invoice

    @patch("app.services.stripe_service.stripe.Transfer.create")
    async def test_successful_transfer(self, mock_transfer, db_session):
        mock_transfer.return_value = MagicMock(id="tr_test_123")

        vendor = await self._create_vendor(db_session, stripe_account_id="acct_test")
        invoice = await self._create_invoice(db_session, vendor.id)

        # Ensure stripe.api_key is truthy so the branch executes
        with patch("app.services.stripe_service.stripe.api_key", "sk_test_fake"):
            result = await execute_vendor_payment(
                invoice_id=invoice.id,
                vendor_id=vendor.id,
                amount_euros=250.00,
                db=db_session,
            )

        assert result["transfer_id"] == "tr_test_123"
        assert result["status"] == "initiated"
        assert "payment_id" in result

        mock_transfer.assert_called_once_with(
            amount=25000,
            currency="eur",
            destination="acct_test",
            metadata={
                "invoice_id": str(invoice.id),
                "vendor_id": str(vendor.id),
            },
        )

    @patch("app.services.stripe_service.stripe.Transfer.create")
    async def test_vendor_no_stripe_account(self, mock_transfer, db_session):
        vendor = await self._create_vendor(db_session, stripe_account_id=None)
        invoice = await self._create_invoice(db_session, vendor.id)

        result = await execute_vendor_payment(
            invoice_id=invoice.id,
            vendor_id=vendor.id,
            amount_euros=100.00,
            db=db_session,
        )

        mock_transfer.assert_not_called()
        assert isinstance(result["transfer_id"], str)
        assert result["transfer_id"].startswith("local_tr_")
        assert result["status"] == "initiated"

    async def test_vendor_not_found(self, db_session):
        fake_invoice_id = uuid.uuid4()
        fake_vendor_id = uuid.uuid4()

        result = await execute_vendor_payment(
            invoice_id=fake_invoice_id,
            vendor_id=fake_vendor_id,
            amount_euros=50.00,
            db=db_session,
        )

        assert result == {"error": "Vendor not found"}

    @patch("app.services.stripe_service.stripe.Transfer.create")
    async def test_stripe_error_handled(self, mock_transfer, db_session):
        mock_transfer.side_effect = stripe_lib.StripeError("Connection error")

        vendor = await self._create_vendor(db_session, stripe_account_id="acct_test")
        invoice = await self._create_invoice(db_session, vendor.id)

        with patch("app.services.stripe_service.stripe.api_key", "sk_test_fake"):
            result = await execute_vendor_payment(
                invoice_id=invoice.id,
                vendor_id=vendor.id,
                amount_euros=200.00,
                db=db_session,
            )

        assert isinstance(result["transfer_id"], str)
        assert result["transfer_id"].startswith("local_tr_")
        assert result["status"] == "initiated"
        assert "payment_id" in result

    @patch("app.services.stripe_service.stripe.Transfer.create")
    async def test_internal_transfer_ids_are_unique(self, mock_transfer, db_session):
        vendor = await self._create_vendor(db_session, stripe_account_id=None)
        invoice_1 = await self._create_invoice(db_session, vendor.id)
        invoice_2 = await self._create_invoice(db_session, vendor.id)

        first = await execute_vendor_payment(
            invoice_id=invoice_1.id,
            vendor_id=vendor.id,
            amount_euros=10.00,
            db=db_session,
        )
        second = await execute_vendor_payment(
            invoice_id=invoice_2.id,
            vendor_id=vendor.id,
            amount_euros=20.00,
            db=db_session,
        )

        assert first["transfer_id"].startswith("local_tr_")
        assert second["transfer_id"].startswith("local_tr_")
        assert first["transfer_id"] != second["transfer_id"]
        mock_transfer.assert_not_called()

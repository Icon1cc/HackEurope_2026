from datetime import datetime, timezone

from app.models.invoice import Invoice
from app.models.vendor import Vendor
from app.models.payment import Payment

INVOICES = "/api/v1/invoices"
BASE = "/api/v1/payments"


class TestPayments:
    async def _create_invoice(self, client):
        resp = await client.post(INVOICES, json={})
        return resp.json()["id"]

    async def test_list_empty(self, client):
        resp = await client.get(BASE)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create(self, client):
        invoice_id = await self._create_invoice(client)
        resp = await client.post(BASE, json={
            "invoice_id": invoice_id,
            "amount": "250.00",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["amount"] == "250.00"
        assert data["currency"] == "EUR"
        assert data["status"] == "initiated"
        assert data["invoice_id"] == invoice_id

    async def test_get_one(self, client):
        invoice_id = await self._create_invoice(client)
        create = await client.post(BASE, json={"invoice_id": invoice_id, "amount": "100"})
        pid = create.json()["id"]

        resp = await client.get(f"{BASE}/{pid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == pid

    async def test_get_not_found(self, client):
        resp = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_get_by_invoice(self, client):
        invoice_id = await self._create_invoice(client)
        await client.post(BASE, json={"invoice_id": invoice_id, "amount": "50"})

        resp = await client.get(f"{BASE}/invoice/{invoice_id}")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_by_status(self, client):
        invoice_id = await self._create_invoice(client)
        await client.post(BASE, json={"invoice_id": invoice_id, "amount": "50"})

        resp = await client.get(f"{BASE}/status/initiated")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_update(self, client):
        invoice_id = await self._create_invoice(client)
        create = await client.post(BASE, json={"invoice_id": invoice_id, "amount": "100"})
        pid = create.json()["id"]

        resp = await client.patch(f"{BASE}/{pid}", json={"status": "confirmed"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

    async def test_delete(self, client):
        invoice_id = await self._create_invoice(client)
        create = await client.post(BASE, json={"invoice_id": invoice_id, "amount": "100"})
        pid = create.json()["id"]

        resp = await client.delete(f"{BASE}/{pid}")
        assert resp.status_code == 204

        resp = await client.get(f"{BASE}/{pid}")
        assert resp.status_code == 404


class TestPaymentConfirmation:
    async def test_confirmation_success(self, client, db_session):
        """Confirmed payment returns vendor IBAN + stripe confirmation."""
        vendor = Vendor(name="IBAN Vendor", category="computing", registered_iban="DE89370400440532013000")
        db_session.add(vendor)
        await db_session.flush()

        invoice = Invoice(vendor_id=vendor.id, total=250.00, status="paid")
        db_session.add(invoice)
        await db_session.flush()

        now = datetime.now(timezone.utc)
        payment = Payment(
            invoice_id=invoice.id,
            stripe_payout_id="tr_confirmed_123",
            amount=250.00,
            currency="EUR",
            status="confirmed",
            initiated_at=now,
            confirmed_at=now,
        )
        db_session.add(payment)
        await db_session.flush()

        resp = await client.get(f"{BASE}/{payment.id}/confirmation")
        assert resp.status_code == 200

        data = resp.json()
        assert data["iban_vendor"] == "DE89370400440532013000"
        assert data["stripe_confirmation"]["transfer_id"] == "tr_confirmed_123"
        assert float(data["stripe_confirmation"]["amount"]) == 250.0
        assert data["stripe_confirmation"]["currency"] == "EUR"
        assert data["stripe_confirmation"]["status"] == "confirmed"
        assert data["stripe_confirmation"]["confirmed_at"] is not None

    async def test_confirmation_not_yet_confirmed(self, client, db_session):
        """Payment still initiated → 400."""
        invoice = Invoice(total=100.00, status="approved")
        db_session.add(invoice)
        await db_session.flush()

        payment = Payment(
            invoice_id=invoice.id,
            stripe_payout_id="tr_pending_456",
            amount=100.00,
            currency="EUR",
            status="initiated",
        )
        db_session.add(payment)
        await db_session.flush()

        resp = await client.get(f"{BASE}/{payment.id}/confirmation")
        assert resp.status_code == 400
        assert "not yet confirmed" in resp.json()["detail"]

    async def test_confirmation_not_found(self, client):
        """Non-existent payment → 404."""
        resp = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000/confirmation")
        assert resp.status_code == 404

    async def test_confirmation_no_vendor_iban(self, client, db_session):
        """Vendor without IBAN → iban_vendor is null."""
        vendor = Vendor(name="No IBAN Vendor", category="computing")
        db_session.add(vendor)
        await db_session.flush()

        invoice = Invoice(vendor_id=vendor.id, total=50.00, status="paid")
        db_session.add(invoice)
        await db_session.flush()

        now = datetime.now(timezone.utc)
        payment = Payment(
            invoice_id=invoice.id,
            stripe_payout_id="tr_no_iban",
            amount=50.00,
            currency="EUR",
            status="confirmed",
            initiated_at=now,
            confirmed_at=now,
        )
        db_session.add(payment)
        await db_session.flush()

        resp = await client.get(f"{BASE}/{payment.id}/confirmation")
        assert resp.status_code == 200
        assert resp.json()["iban_vendor"] is None

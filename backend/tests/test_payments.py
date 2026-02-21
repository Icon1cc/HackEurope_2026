import pytest

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

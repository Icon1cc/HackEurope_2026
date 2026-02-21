import pytest

INVOICES = "/api/v1/invoices"
BASE = "/api/v1/items"


class TestItems:
    async def _create_invoice(self, client):
        resp = await client.post(INVOICES, json={})
        return resp.json()["id"]

    async def test_list_empty(self, client):
        resp = await client.get(BASE)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create(self, client):
        invoice_id = await self._create_invoice(client)
        resp = await client.post(BASE, json={
            "invoice_id": invoice_id,
            "description": "AWS EC2 Instance",
            "quantity": "730.0",
            "unit_price": "0.046",
            "total_price": "33.58",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["description"] == "AWS EC2 Instance"
        assert data["quantity"] == "730.0"
        assert data["invoice_id"] == invoice_id

    async def test_get_one(self, client):
        invoice_id = await self._create_invoice(client)
        create = await client.post(BASE, json={
            "invoice_id": invoice_id,
            "description": "S3 Storage",
        })
        item_id = create.json()["id"]

        resp = await client.get(f"{BASE}/{item_id}")
        assert resp.status_code == 200
        assert resp.json()["description"] == "S3 Storage"

    async def test_get_not_found(self, client):
        resp = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_get_by_invoice(self, client):
        invoice_id = await self._create_invoice(client)
        await client.post(BASE, json={"invoice_id": invoice_id, "description": "Item A"})
        await client.post(BASE, json={"invoice_id": invoice_id, "description": "Item B"})

        resp = await client.get(f"{BASE}/invoice/{invoice_id}")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 2
        descriptions = {i["description"] for i in items}
        assert "Item A" in descriptions
        assert "Item B" in descriptions

    async def test_update(self, client):
        invoice_id = await self._create_invoice(client)
        create = await client.post(BASE, json={
            "invoice_id": invoice_id,
            "description": "Old Description",
        })
        item_id = create.json()["id"]

        resp = await client.patch(f"{BASE}/{item_id}", json={"description": "New Description"})
        assert resp.status_code == 200
        assert resp.json()["description"] == "New Description"

    async def test_delete(self, client):
        invoice_id = await self._create_invoice(client)
        create = await client.post(BASE, json={
            "invoice_id": invoice_id,
            "description": "DeleteMe",
        })
        item_id = create.json()["id"]

        resp = await client.delete(f"{BASE}/{item_id}")
        assert resp.status_code == 204

        resp = await client.get(f"{BASE}/{item_id}")
        assert resp.status_code == 404

    async def test_invoice_includes_items(self, client):
        """Items appear nested in the invoice response."""
        invoice_id = await self._create_invoice(client)
        await client.post(BASE, json={
            "invoice_id": invoice_id,
            "description": "Nested Item",
            "quantity": "10",
            "unit_price": "5.00",
            "total_price": "50.00",
        })

        resp = await client.get(f"{INVOICES}/{invoice_id}")
        assert resp.status_code == 200
        invoice = resp.json()
        assert len(invoice["items"]) >= 1
        assert invoice["items"][0]["description"] == "Nested Item"

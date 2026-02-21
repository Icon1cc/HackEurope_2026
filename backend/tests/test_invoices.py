import pytest

BASE = "/api/v1/invoices"


class TestInvoices:
    async def test_list_empty(self, client):
        resp = await client.get(BASE)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_minimal(self, client):
        resp = await client.post(BASE, json={})
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["auto_approved"] is False
        assert data["items"] == []

    async def test_create_with_url(self, client):
        resp = await client.post(BASE, json={"raw_file_url": "https://example.com/invoice.pdf"})
        assert resp.status_code == 201
        assert resp.json()["raw_file_url"] == "https://example.com/invoice.pdf"

    async def test_get_one(self, client):
        create = await client.post(BASE, json={})
        iid = create.json()["id"]

        resp = await client.get(f"{BASE}/{iid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == iid

    async def test_get_not_found(self, client):
        resp = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_update_status(self, client):
        create = await client.post(BASE, json={})
        iid = create.json()["id"]

        resp = await client.patch(f"{BASE}/{iid}", json={"status": "flagged"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "flagged"

    async def test_update_extracted_data(self, client):
        create = await client.post(BASE, json={})
        iid = create.json()["id"]

        resp = await client.patch(f"{BASE}/{iid}", json={
            "extracted_data": {"invoice_number": "INV-001"},
            "confidence_score": 85,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["extracted_data"]["invoice_number"] == "INV-001"
        assert data["confidence_score"] == 85

    async def test_get_flagged(self, client):
        # Create a flagged invoice
        create = await client.post(BASE, json={})
        iid = create.json()["id"]
        await client.patch(f"{BASE}/{iid}", json={"status": "flagged"})

        resp = await client.get(f"{BASE}/flagged")
        assert resp.status_code == 200
        flagged = resp.json()
        assert any(i["id"] == iid for i in flagged)

    async def test_get_by_status(self, client):
        create = await client.post(BASE, json={})
        iid = create.json()["id"]

        resp = await client.get(f"{BASE}/status/pending")
        assert resp.status_code == 200
        assert any(i["id"] == iid for i in resp.json())

    async def test_delete(self, client):
        create = await client.post(BASE, json={})
        iid = create.json()["id"]

        resp = await client.delete(f"{BASE}/{iid}")
        assert resp.status_code == 204

        resp = await client.get(f"{BASE}/{iid}")
        assert resp.status_code == 404

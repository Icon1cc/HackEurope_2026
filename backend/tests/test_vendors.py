import pytest

BASE = "/api/v1/vendors"


class TestVendors:
    async def test_list_empty(self, client):
        resp = await client.get(BASE)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_minimal(self, client):
        resp = await client.post(BASE, json={"name": "CloudHost Pro"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "CloudHost Pro"
        assert data["category"] == "computing"
        assert data["trust_score"] == "0.5"
        assert data["invoice_count"] == 0

    async def test_create_full(self, client):
        resp = await client.post(BASE, json={
            "name": "DataCenter EU",
            "category": "storage",
            "email": "sales@dc.eu",
            "registered_iban": "DE89370400440532013000",
            "vendor_address": "123 Tech Park",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "sales@dc.eu"
        assert data["vendor_address"] == "123 Tech Park"

    async def test_get_one(self, client):
        create = await client.post(BASE, json={"name": "GetVendor"})
        vid = create.json()["id"]

        resp = await client.get(f"{BASE}/{vid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "GetVendor"

    async def test_get_not_found(self, client):
        resp = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_update(self, client):
        create = await client.post(BASE, json={"name": "OldVendor"})
        vid = create.json()["id"]

        resp = await client.patch(f"{BASE}/{vid}", json={"name": "NewVendor", "category": "network"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "NewVendor"
        assert resp.json()["category"] == "network"

    async def test_delete(self, client):
        create = await client.post(BASE, json={"name": "DeleteVendor"})
        vid = create.json()["id"]

        resp = await client.delete(f"{BASE}/{vid}")
        assert resp.status_code == 204

        resp = await client.get(f"{BASE}/{vid}")
        assert resp.status_code == 404

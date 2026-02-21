import pytest

INVOICES = "/api/v1/invoices"
VENDORS = "/api/v1/vendors"
BASE = "/api/v1/overrides"


class TestOverrides:
    async def _setup(self, client):
        inv = await client.post(INVOICES, json={})
        ven = await client.post(VENDORS, json={"name": "TestVendor"})
        return inv.json()["id"], ven.json()["id"]

    async def test_list_empty(self, client):
        resp = await client.get(BASE)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create(self, client):
        invoice_id, vendor_id = await self._setup(client)
        resp = await client.post(BASE, json={
            "invoice_id": invoice_id,
            "vendor_id": vendor_id,
            "agent_recommendation": "approve",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["agent_recommendation"] == "approve"
        assert data["human_decision"] is None
        assert data["agreed"] is None

    async def test_get_one(self, client):
        invoice_id, vendor_id = await self._setup(client)
        create = await client.post(BASE, json={
            "invoice_id": invoice_id,
            "vendor_id": vendor_id,
            "agent_recommendation": "reject",
        })
        oid = create.json()["id"]

        resp = await client.get(f"{BASE}/{oid}")
        assert resp.status_code == 200
        assert resp.json()["agent_recommendation"] == "reject"

    async def test_get_not_found(self, client):
        resp = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_update_human_decision(self, client):
        invoice_id, vendor_id = await self._setup(client)
        create = await client.post(BASE, json={
            "invoice_id": invoice_id,
            "vendor_id": vendor_id,
            "agent_recommendation": "approve",
        })
        oid = create.json()["id"]

        resp = await client.patch(f"{BASE}/{oid}", json={
            "human_decision": "reject",
            "agreed": False,
            "override_reason": "suspicious amount",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["human_decision"] == "reject"
        assert data["agreed"] is False
        assert data["override_reason"] == "suspicious amount"

    async def test_get_by_invoice(self, client):
        invoice_id, vendor_id = await self._setup(client)
        await client.post(BASE, json={
            "invoice_id": invoice_id,
            "vendor_id": vendor_id,
            "agent_recommendation": "approve",
        })

        resp = await client.get(f"{BASE}/invoice/{invoice_id}")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_by_vendor(self, client):
        invoice_id, vendor_id = await self._setup(client)
        await client.post(BASE, json={
            "invoice_id": invoice_id,
            "vendor_id": vendor_id,
            "agent_recommendation": "approve",
        })

        resp = await client.get(f"{BASE}/vendor/{vendor_id}")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_delete(self, client):
        invoice_id, vendor_id = await self._setup(client)
        create = await client.post(BASE, json={
            "invoice_id": invoice_id,
            "vendor_id": vendor_id,
            "agent_recommendation": "approve",
        })
        oid = create.json()["id"]

        resp = await client.delete(f"{BASE}/{oid}")
        assert resp.status_code == 204

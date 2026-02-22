from decimal import Decimal
import pytest

BASE = "/api/v1/vendors"
INVOICES_BASE = "/api/v1/invoices"


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

    async def test_trust_score_is_average_of_vendor_invoice_scores(self, client):
        create_vendor = await client.post(BASE, json={"name": "Metrics Vendor"})
        assert create_vendor.status_code == 201
        vendor_id = create_vendor.json()["id"]

        create_first = await client.post(INVOICES_BASE, json={"vendor_id": vendor_id})
        assert create_first.status_code == 201
        first_invoice_id = create_first.json()["id"]

        create_second = await client.post(INVOICES_BASE, json={"vendor_id": vendor_id})
        assert create_second.status_code == 201
        second_invoice_id = create_second.json()["id"]

        # Third invoice has no explicit score and should count as 0 in average.
        create_third = await client.post(INVOICES_BASE, json={"vendor_id": vendor_id})
        assert create_third.status_code == 201

        first_patch = await client.patch(f"{INVOICES_BASE}/{first_invoice_id}", json={"confidence_score": 80})
        assert first_patch.status_code == 200

        second_patch = await client.patch(f"{INVOICES_BASE}/{second_invoice_id}", json={"confidence_score": 60})
        assert second_patch.status_code == 200

        vendor_resp = await client.get(f"{BASE}/{vendor_id}")
        assert vendor_resp.status_code == 200
        vendor_payload = vendor_resp.json()

        # ((80 + 60 + 0) / 3) / 100 = 0.4666...
        trust_score = Decimal(vendor_payload["trust_score"])
        assert vendor_payload["invoice_count"] == 3
        assert trust_score.quantize(Decimal("0.0001")) == Decimal("0.4667")

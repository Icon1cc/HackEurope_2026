import pytest

BASE = "/api/v1/pricing"


class TestPricing:
    async def test_list_empty(self, client):
        resp = await client.get(BASE)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_sync_status(self, client):
        resp = await client.get(f"{BASE}/sync/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_skus" in data
        assert "by_vendor" in data
        assert "by_category" in data
        assert "message" in data

    async def test_get_not_found(self, client):
        resp = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_invoice_check_empty(self, client):
        resp = await client.post(f"{BASE}/invoice/check", json={"items": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_billed"] == "0"
        assert data["total_expected"] == "0"
        assert data["items"] == []

    async def test_invoice_check_no_match(self, client):
        resp = await client.post(f"{BASE}/invoice/check", json={
            "items": [{
                "vendor": "aws",
                "instance_type": "nonexistent.9xlarge",
                "hours": "100",
                "billed_amount": "999.99",
            }]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "NO_MATCH"

    async def test_list_with_filters(self, client):
        resp = await client.get(BASE, params={"vendor": "aws", "category": "Compute"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

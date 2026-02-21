import pytest

BASE = "/api/v1/market-data"


class TestMarketData:
    async def test_list_empty(self, client):
        resp = await client.get(BASE)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create(self, client):
        resp = await client.post(BASE, json={
            "name": "m5.xlarge",
            "category": "Compute",
            "price_per_unit": "0.192",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "m5.xlarge"
        assert data["category"] == "Compute"
        assert data["price_per_unit"] == "0.192"

    async def test_get_one(self, client):
        create = await client.post(BASE, json={
            "name": "t3.micro",
            "category": "Compute",
            "price_per_unit": "0.0104",
        })
        mid = create.json()["id"]

        resp = await client.get(f"{BASE}/{mid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "t3.micro"

    async def test_get_not_found(self, client):
        resp = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_get_by_category(self, client):
        await client.post(BASE, json={
            "name": "gp3-volume",
            "category": "Storage",
            "price_per_unit": "0.08",
        })

        resp = await client.get(f"{BASE}/category/Storage")
        assert resp.status_code == 200
        assert any(d["category"] == "Storage" for d in resp.json())

    async def test_update(self, client):
        create = await client.post(BASE, json={
            "name": "old-sku",
            "category": "Compute",
            "price_per_unit": "1.00",
        })
        mid = create.json()["id"]

        resp = await client.patch(f"{BASE}/{mid}", json={"price_per_unit": "2.00"})
        assert resp.status_code == 200
        assert resp.json()["price_per_unit"] == "2.00"

    async def test_delete(self, client):
        create = await client.post(BASE, json={
            "name": "delete-sku",
            "category": "CDN",
            "price_per_unit": "0.01",
        })
        mid = create.json()["id"]

        resp = await client.delete(f"{BASE}/{mid}")
        assert resp.status_code == 204

        resp = await client.get(f"{BASE}/{mid}")
        assert resp.status_code == 404

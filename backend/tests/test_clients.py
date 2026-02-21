import pytest

BASE = "/api/v1/clients"


class TestClients:
    async def test_list_empty(self, client):
        resp = await client.get(BASE)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create(self, client):
        resp = await client.post(BASE, json={"name_of_business": "TestCorp"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name_of_business"] == "TestCorp"
        assert "id" in data
        assert "created_at" in data

    async def test_get_one(self, client):
        create = await client.post(BASE, json={"name_of_business": "GetMe"})
        cid = create.json()["id"]

        resp = await client.get(f"{BASE}/{cid}")
        assert resp.status_code == 200
        assert resp.json()["name_of_business"] == "GetMe"

    async def test_get_not_found(self, client):
        resp = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_update(self, client):
        create = await client.post(BASE, json={"name_of_business": "OldName"})
        cid = create.json()["id"]

        resp = await client.patch(f"{BASE}/{cid}", json={"name_of_business": "NewName"})
        assert resp.status_code == 200
        assert resp.json()["name_of_business"] == "NewName"

    async def test_delete(self, client):
        create = await client.post(BASE, json={"name_of_business": "DeleteMe"})
        cid = create.json()["id"]

        resp = await client.delete(f"{BASE}/{cid}")
        assert resp.status_code == 204

        resp = await client.get(f"{BASE}/{cid}")
        assert resp.status_code == 404

    async def test_delete_not_found(self, client):
        resp = await client.delete(f"{BASE}/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

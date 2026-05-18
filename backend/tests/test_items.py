from httpx import AsyncClient


async def test_create_item(client: AsyncClient) -> None:
    response = await client.post("/api/items/", json={"title": "Test item"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test item"
    assert "id" in data
    assert "created_at" in data


async def test_list_items(client: AsyncClient) -> None:
    await client.post("/api/items/", json={"title": "First"})
    await client.post("/api/items/", json={"title": "Second"})

    response = await client.get("/api/items/")
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert titles == ["First", "Second"]

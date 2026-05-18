import pytest
from httpx import AsyncClient


@pytest.mark.slow
async def test_bulk_items_roundtrip(client: AsyncClient) -> None:
    # Demonstrates the @slow tier: 1000 inserts is intentionally heavier
    # than a fast-tier test. The slow tier runs nightly, or on PRs when
    # path triggers pull this file in (see scripts/path_triggers.sh).
    n = 1000
    for i in range(n):
        r = await client.post("/api/items/", json={"title": f"item-{i}"})
        assert r.status_code == 201

    response = await client.get("/api/items/")
    assert response.status_code == 200
    assert len(response.json()) == n

async def test_healthz(client):
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


async def test_dummy_endpoint(client):
    response = await client.get("/dummy")
    assert response.status_code == 200
    body = response.json()
    assert "message" in body

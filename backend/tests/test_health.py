import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

def test_root_endpoint():
    async def _run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert "framework" in data
        assert data["docs_url"] == "/docs"
    asyncio.run(_run())

def test_health_endpoint():
    async def _run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "ollama_connected" in data
        assert "docker_available" in data
        assert "model" in data
    asyncio.run(_run())

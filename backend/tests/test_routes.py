import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

def test_api_routes():
    async def _run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Health
            res = await client.get("/api/health")
            assert res.status_code == 200

            # 2. Stats
            res = await client.get("/api/stats")
            assert res.status_code == 200
            data = res.json()
            assert "efficiency" in data
            assert "accuracy" in data

            # 3. History
            res = await client.get("/api/history")
            assert res.status_code == 200

            # 4. Projects
            res = await client.get("/api/projects")
            assert res.status_code == 200

            # 5. Models
            res = await client.get("/api/models")
            assert res.status_code == 200

    asyncio.run(_run())

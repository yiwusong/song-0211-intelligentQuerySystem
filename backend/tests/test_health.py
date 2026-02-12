"""健康检查接口测试"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    # 无数据库时返回 degraded，有数据库时返回 ok
    assert data["status"] in ("ok", "degraded")
    assert data["service"] == "松哥的智能数据分析系统"
    assert "model" in data
    assert "database" in data
    assert "schema_index" in data

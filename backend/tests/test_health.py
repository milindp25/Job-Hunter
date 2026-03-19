from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_healthy(client: AsyncClient) -> None:
    """Health check endpoint responds with healthy status."""
    response = await client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "checks" in data
    assert "version" in data
    assert data["checks"]["database"] == "ok"


@pytest.mark.asyncio
async def test_health_check_includes_version(client: AsyncClient) -> None:
    """Health check response includes the application version."""
    response = await client.get("/api/health")
    data = response.json()
    assert data["version"] == "1.0.0"

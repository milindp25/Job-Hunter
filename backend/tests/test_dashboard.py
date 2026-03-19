from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_stats_requires_auth(client: AsyncClient) -> None:
    """Dashboard stats endpoint rejects unauthenticated requests."""
    response = await client.get("/api/dashboard/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_stats_returns_structure(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Dashboard stats endpoint returns the expected response shape."""
    response = await client.get("/api/dashboard/stats", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "total_saved_jobs" in data
    assert "total_matches" in data
    assert "resumes_count" in data
    assert "avg_match_score" in data
    assert "avg_ats_score" in data
    assert "recent_matches" in data
    assert "weekly_activity" in data

    # For a new user all counts should be zero
    assert data["total_saved_jobs"] == 0
    assert data["total_matches"] == 0
    assert data["resumes_count"] == 0
    assert data["avg_match_score"] is None
    assert data["avg_ats_score"] is None
    assert data["recent_matches"] == []
    assert isinstance(data["weekly_activity"], list)
    assert len(data["weekly_activity"]) == 4

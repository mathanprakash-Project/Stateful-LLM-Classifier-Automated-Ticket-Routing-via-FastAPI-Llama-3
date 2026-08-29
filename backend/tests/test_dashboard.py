"""
Tests for Dashboard analytics and statistics endpoint.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_stats(client: AsyncClient):
    # Login as Manager Alice
    login_resp = await client.post(
        "/auth/login",
        json={"email": "alice@company.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch stats
    stats_resp = await client.get("/dashboard/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "total_tickets" in stats
    assert "open_tickets" in stats
    assert "in_progress_tickets" in stats
    assert "resolved_tickets" in stats
    assert "closed_tickets" in stats
    assert "recent_tickets" in stats


"""
Tests for authentication, password hashing, and token issuance.
"""

import pytest
from httpx import AsyncClient
from app.auth.password import get_password_hash, verify_password


def test_password_hashing():
    pwd = "secretpassword123"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        json={"email": "john@company.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "john@company.com"
    assert "user" in data["user"]["roles"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        json={"email": "john@company.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_get_profile(client: AsyncClient):
    # Login first
    login_resp = await client.post(
        "/auth/login",
        json={"email": "john@company.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # Access /auth/me
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "john@company.com"
    assert "ticket:create" in data["permissions"]


"""
Tests for Ticket CRUD, validation, comments, and history recording.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_read_ticket(client: AsyncClient):
    # 1. Login as John Doe
    login_resp = await client.post(
        "/auth/login",
        json={"email": "john@company.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Categories
    cats_resp = await client.get("/categories")
    assert cats_resp.status_code == 200
    categories = cats_resp.json()
    assert len(categories) > 0
    cat_id = categories[0]["id"]
    sub_id = categories[0]["subcategories"][0]["id"] if categories[0]["subcategories"] else None

    # 3. Create Ticket
    ticket_payload = {
        "title": "Laptop Screen Flickering",
        "description": "My external monitor keeps disconnecting and flickering when plugged into HDMI.",
        "category_id": cat_id,
        "subcategory_id": sub_id,
        "priority": "high",
        "meta_info": {"device": "Dell XPS 15"},
    }
    create_resp = await client.post("/tickets", json=ticket_payload, headers=headers)
    assert create_resp.status_code == 201
    ticket = create_resp.json()
    assert ticket["ticket_number"].startswith("TKT-")
    assert ticket["status"] == "open"
    assert ticket["title"] == "Laptop Screen Flickering"
    ticket_id = ticket["id"]

    # 4. Read Ticket
    get_resp = await client.get(f"/tickets/{ticket_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == ticket_id
    assert len(get_resp.json()["history"]) >= 1

    # 5. Add Comment
    comment_resp = await client.post(
        f"/tickets/{ticket_id}/comments",
        json={"content": "I tried restarting and changing the cable, but issue persists."},
        headers=headers,
    )
    assert comment_resp.status_code == 201
    assert comment_resp.json()["content"].startswith("I tried restarting")


@pytest.mark.asyncio
async def test_ticket_status_transition_as_agent(client: AsyncClient):
    # User creates ticket
    u_login = await client.post("/auth/login", json={"email": "john@company.com", "password": "password123"})
    u_headers = {"Authorization": f"Bearer {u_login.json()['access_token']}"}

    cats = (await client.get("/categories")).json()
    t_resp = await client.post(
        "/tickets",
        json={
            "title": "Cannot Connect to VPN",
            "description": "VPN client times out on handshake.",
            "category_id": cats[0]["id"],
            "priority": "medium",
        },
        headers=u_headers,
    )
    ticket_id = t_resp.json()["id"]

    # Agent Bob logs in and updates status to assigned
    agent_login = await client.post("/auth/login", json={"email": "bob@company.com", "password": "password123"})
    agent_headers = {"Authorization": f"Bearer {agent_login.json()['access_token']}"}

    update_resp = await client.patch(
        f"/tickets/{ticket_id}",
        json={"status": "assigned", "comment": "Assigned to Bob for investigation."},
        headers=agent_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "assigned"


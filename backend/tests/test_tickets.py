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
            "activity_code": "NETWORK"
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


@pytest.mark.asyncio
async def test_approve_restricted_operation(client: AsyncClient):
    admin_login = await client.post("/auth/login", json={"email": "admin@company.com", "password": "password123"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    user_login = await client.post("/auth/login", json={"email": "john@company.com", "password": "password123"})
    user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

    cats = (await client.get("/categories")).json()
    
    t_resp = await client.post(
        "/tickets",
        json={
            "title": "Data Transfer",
            "description": "Transfer data",
            "category_id": cats[0]["id"],
            "priority": "high",
            "requires_admin_approval": True,
            "operation_status": "pending",
            "activity_code": "CLIENT_DATA_TRANSFER"
        },
        headers=user_headers,
    )
    ticket_id = t_resp.json()["id"]
    
    # Needs to be in pending_admin_approval which is the default when requires_admin_approval is True
    assert t_resp.json()["status"] == "pending_admin_approval"
    
    approve_resp = await client.post(f"/tickets/{ticket_id}/approve", headers=admin_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"
    assert approve_resp.json()["operation_status"] == "approved"


@pytest.mark.asyncio
async def test_reject_restricted_operation(client: AsyncClient):
    admin_login = await client.post("/auth/login", json={"email": "admin@company.com", "password": "password123"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    user_login = await client.post("/auth/login", json={"email": "john@company.com", "password": "password123"})
    user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

    cats = (await client.get("/categories")).json()
    
    t_resp = await client.post(
        "/tickets",
        json={
            "title": "Data Transfer",
            "description": "Transfer data",
            "category_id": cats[0]["id"],
            "priority": "high",
            "requires_admin_approval": True,
            "operation_status": "pending",
            "activity_code": "CLIENT_DATA_TRANSFER"
        },
        headers=user_headers,
    )
    ticket_id = t_resp.json()["id"]
    
    reject_resp = await client.post(f"/tickets/{ticket_id}/reject", json={"reason": "Not allowed"}, headers=admin_headers)
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"
    assert reject_resp.json()["operation_status"] == "rejected"


@pytest.mark.asyncio
async def test_route_ticket(client: AsyncClient):
    manager_login = await client.post("/auth/login", json={"email": "alice@company.com", "password": "password123"})
    manager_headers = {"Authorization": f"Bearer {manager_login.json()['access_token']}"}

    user_login = await client.post("/auth/login", json={"email": "john@company.com", "password": "password123"})
    user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

    cats = (await client.get("/categories")).json()
    
    t_resp = await client.post(
        "/tickets",
        json={
            "title": "Database issue",
            "description": "DB slow",
            "category_id": cats[0]["id"],
            "priority": "high",
            "responsible_team": "DATABASE",
            "activity_code": "DATABASE"
        },
        headers=user_headers,
    )
    ticket_id = t_resp.json()["id"]
    # should be pending_manager_routing
    assert t_resp.json()["status"] == "pending_manager_routing"
    
    route_resp = await client.post(f"/tickets/{ticket_id}/route", json={"target_team": "DATABASE_ADMINS"}, headers=manager_headers)
    assert route_resp.status_code == 200
    assert route_resp.json()["status"] == "routed"
    assert route_resp.json()["routed_to_team"] == "DATABASE_ADMINS"


@pytest.mark.asyncio
async def test_user_cannot_approve(client: AsyncClient):
    admin_login = await client.post("/auth/login", json={"email": "admin@company.com", "password": "password123"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    
    user_login = await client.post("/auth/login", json={"email": "john@company.com", "password": "password123"})
    user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}
    
    cats = (await client.get("/categories")).json()
    
    t_resp = await client.post(
        "/tickets",
        json={
            "title": "Data Transfer",
            "description": "Transfer data",
            "category_id": cats[0]["id"],
            "priority": "high",
            "requires_admin_approval": True,
            "operation_status": "pending",
            "activity_code": "CLIENT_DATA_TRANSFER"
        },
        headers=user_headers,
    )
    ticket_id = t_resp.json()["id"]
    
    approve_resp = await client.post(f"/tickets/{ticket_id}/approve", headers=user_headers)
    assert approve_resp.status_code in [403, 404, 422, 400]


@pytest.mark.asyncio
async def test_manager_can_delete_ticket(client: AsyncClient):
    manager_login = await client.post("/auth/login", json={"email": "alice@company.com", "password": "password123"})
    manager_headers = {"Authorization": f"Bearer {manager_login.json()['access_token']}"}

    user_login = await client.post("/auth/login", json={"email": "john@company.com", "password": "password123"})
    user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

    cats = (await client.get("/categories")).json()
    t_resp = await client.post(
        "/tickets",
        json={
            "title": "Ticket to be Deleted",
            "description": "This ticket was created by accident and must be removed.",
            "category_id": cats[0]["id"],
            "priority": "low",
        },
        headers=user_headers,
    )
    assert t_resp.status_code == 201
    ticket_id = t_resp.json()["id"]

    # 1. Attempt to delete while ticket is still OPEN -> should fail (422)
    del_open_resp = await client.delete(f"/tickets/{ticket_id}", headers=manager_headers)
    assert del_open_resp.status_code == 422
    assert "only be deleted after they are resolved" in del_open_resp.text

    # 2. Transition ticket to RESOLVED
    # Start work & resolve
    await client.post(f"/tickets/{ticket_id}/start-work", headers=manager_headers)
    await client.post(f"/tickets/{ticket_id}/complete-work", json={"notes": "Issue resolved."}, headers=manager_headers)

    # 3. Delete ticket as manager after it is resolved -> should succeed (200)
    del_resp = await client.delete(f"/tickets/{ticket_id}", headers=manager_headers)
    assert del_resp.status_code == 200
    assert "deleted successfully" in del_resp.json()["message"]

    # 4. Verify ticket is permanently gone
    get_resp = await client.get(f"/tickets/{ticket_id}", headers=manager_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_non_manager_cannot_delete_ticket(client: AsyncClient):
    user_login = await client.post("/auth/login", json={"email": "john@company.com", "password": "password123"})
    user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

    agent_login = await client.post("/auth/login", json={"email": "bob@company.com", "password": "password123"})
    agent_headers = {"Authorization": f"Bearer {agent_login.json()['access_token']}"}

    cats = (await client.get("/categories")).json()
    t_resp = await client.post(
        "/tickets",
        json={
            "title": "User Ticket",
            "description": "User created ticket.",
            "category_id": cats[0]["id"],
            "priority": "medium",
        },
        headers=user_headers,
    )
    assert t_resp.status_code == 201
    ticket_id = t_resp.json()["id"]

    # Regular user attempt to delete -> 403 Forbidden
    del_user_resp = await client.delete(f"/tickets/{ticket_id}", headers=user_headers)
    assert del_user_resp.status_code == 403

    # Agent attempt to delete -> 403 Forbidden
    del_agent_resp = await client.delete(f"/tickets/{ticket_id}", headers=agent_headers)
    assert del_agent_resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_nonexistent_ticket(client: AsyncClient):
    manager_login = await client.post("/auth/login", json={"email": "alice@company.com", "password": "password123"})
    manager_headers = {"Authorization": f"Bearer {manager_login.json()['access_token']}"}

    del_resp = await client.delete("/tickets/00000000-0000-0000-0000-000000000000", headers=manager_headers)
    assert del_resp.status_code == 404


@pytest.mark.asyncio
async def test_non_user_cannot_create_ticket(client: AsyncClient):
    agent_login = await client.post("/auth/login", json={"email": "bob@company.com", "password": "password123"})
    agent_headers = {"Authorization": f"Bearer {agent_login.json()['access_token']}"}

    cats = (await client.get("/categories")).json()
    create_resp = await client.post(
        "/tickets",
        json={
            "title": "Agent Attempted Ticket",
            "description": "Agents cannot create tickets",
            "category_id": cats[0]["id"],
            "priority": "low",
        },
        headers=agent_headers,
    )
    assert create_resp.status_code in [403, 422]
    assert "Only requester user profile is authorized to create tickets" in create_resp.text


@pytest.mark.asyncio
async def test_reopen_ticket_limit_max_3_times(client: AsyncClient):
    user_login = await client.post("/auth/login", json={"email": "venu@company.com", "password": "password123"})
    if user_login.status_code != 200:
        user_login = await client.post("/auth/login", json={"email": "john@company.com", "password": "password123"})
    user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

    agent_login = await client.post("/auth/login", json={"email": "eegan@company.com", "password": "password123"})
    if agent_login.status_code != 200:
        agent_login = await client.post("/auth/login", json={"email": "bob@company.com", "password": "password123"})
    agent_headers = {"Authorization": f"Bearer {agent_login.json()['access_token']}"}

    cats = (await client.get("/categories")).json()
    t_resp = await client.post(
        "/tickets",
        json={
            "title": "Reopen Limit Verification Ticket",
            "description": "Verify that a ticket can be reopened at most 3 times.",
            "category_id": cats[0]["id"],
            "priority": "medium",
        },
        headers=user_headers,
    )
    assert t_resp.status_code == 201
    ticket_id = t_resp.json()["id"]

    # Agent starts and resolves ticket first time
    await client.post(f"/tickets/{ticket_id}/start-work", headers=agent_headers)
    res1 = await client.post(f"/tickets/{ticket_id}/complete-work", json={"notes": "Resolved attempt 1"}, headers=agent_headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "resolved"

    # 1. First Reopen (Attempt 1 of 3) -> Allowed
    reopen1 = await client.post(f"/tickets/{ticket_id}/reopen", headers=user_headers)
    assert reopen1.status_code == 200
    assert reopen1.json()["status"] == "reopened"

    # Agent starts and resolves ticket second time
    await client.post(f"/tickets/{ticket_id}/start-work", headers=agent_headers)
    res2 = await client.post(f"/tickets/{ticket_id}/complete-work", json={"notes": "Resolved attempt 2"}, headers=agent_headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "resolved"

    # 2. Second Reopen (Attempt 2 of 3) -> Allowed
    reopen2 = await client.post(f"/tickets/{ticket_id}/reopen", headers=user_headers)
    assert reopen2.status_code == 200
    assert reopen2.json()["status"] == "reopened"

    # Agent starts and resolves ticket third time
    await client.post(f"/tickets/{ticket_id}/start-work", headers=agent_headers)
    res3 = await client.post(f"/tickets/{ticket_id}/complete-work", json={"notes": "Resolved attempt 3"}, headers=agent_headers)
    assert res3.status_code == 200
    assert res3.json()["status"] == "resolved"

    # 3. Third Reopen (Attempt 3 of 3) -> Allowed
    reopen3 = await client.post(f"/tickets/{ticket_id}/reopen", headers=user_headers)
    assert reopen3.status_code == 200
    assert reopen3.json()["status"] == "reopened"

    # Agent starts and resolves ticket fourth time
    await client.post(f"/tickets/{ticket_id}/start-work", headers=agent_headers)
    res4 = await client.post(f"/tickets/{ticket_id}/complete-work", json={"notes": "Resolved attempt 4"}, headers=agent_headers)
    assert res4.status_code == 200
    assert res4.json()["status"] == "resolved"

    # 4. Fourth Reopen -> Must be BLOCKED (422)
    reopen4 = await client.post(f"/tickets/{ticket_id}/reopen", headers=user_headers)
    assert reopen4.status_code == 422
    assert "maximum limit of 3 reopens" in reopen4.text


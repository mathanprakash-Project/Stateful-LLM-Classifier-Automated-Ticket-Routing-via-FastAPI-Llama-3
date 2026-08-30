import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_restricted_operation_full_workflow(client: AsyncClient):
    """Test: create ticket -> set to pending_admin_approval -> admin approves -> admin executes -> resolved"""
    # 1. Login as admin
    login_res = await client.post("/auth/login", json={"email": "admin@company.com", "password": "password123"})
    admin_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}
    
    # 2. Create ticket (use first available category)
    cats_res = await client.get("/categories")
    cat = cats_res.json()[0]
    ticket_data = {
        "title": "Upgrade app to v5.0",
        "description": "Need version upgrade for production",
        "category_id": cat["id"],
        "priority": "high",
        "activity_code": "APPLICATION_VERSION",
        "technical_scope": "application",
        "requires_admin_approval": True,
        "operation_status": "pending"
    }
    create_res = await client.post("/tickets", json=ticket_data, headers=admin_headers)
    assert create_res.status_code == 201
    ticket = create_res.json()
    ticket_id = ticket["id"]
    
    # 3. Transition to pending_admin_approval
    # By default, it might be in pending_admin_approval based on requires_admin_approval
    # but let's just make sure
    update_res = await client.patch(f"/tickets/{ticket_id}", 
        json={"status": "pending_admin_approval", "comment": "Needs approval"},
        headers=admin_headers)
    assert update_res.status_code == 200
    
    # 4. Admin approves
    approve_res = await client.post(f"/tickets/{ticket_id}/approve", headers=admin_headers)
    assert approve_res.status_code == 200
    approved_ticket = approve_res.json()
    assert approved_ticket["status"] == "approved"
    assert approved_ticket["operation_status"] == "approved"
    
    # 5. Admin executes
    exec_res = await client.post(f"/tickets/{ticket_id}/execute", headers=admin_headers)
    assert exec_res.status_code == 200
    executed_ticket = exec_res.json()
    assert executed_ticket["status"] == "resolved"
    assert executed_ticket["operation_status"] == "completed"


@pytest.mark.asyncio
async def test_manager_routing_workflow(client: AsyncClient):
    """Test: create ticket -> set to pending_manager_routing -> manager routes"""
    # 1. Login as manager
    login_res = await client.post("/auth/login", json={"email": "alice@company.com", "password": "password123"})
    manager_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}
    
    # 2. Create ticket
    cats_res = await client.get("/categories")
    cat = cats_res.json()[0]
    ticket_data = {
        "title": "Database server is slow",
        "description": "The production database has high latency",
        "category_id": cat["id"],
        "priority": "high",
        "activity_code": "DATABASE",
        "technical_scope": "out_of_application_scope",
        "responsible_team": "DATABASE"
    }
    create_res = await client.post("/tickets", json=ticket_data, headers=manager_headers)
    assert create_res.status_code == 201
    ticket_id = create_res.json()["id"]
    
    # 3. Transition to pending_manager_routing
    update_res = await client.patch(f"/tickets/{ticket_id}",
        json={"status": "pending_manager_routing", "comment": "Needs routing"},
        headers=manager_headers)
    assert update_res.status_code == 200
    
    # 4. Manager routes
    route_res = await client.post(f"/tickets/{ticket_id}/route",
        json={"target_team": "DATABASE"},
        headers=manager_headers)
    assert route_res.status_code == 200
    routed = route_res.json()
    assert routed["status"] == "routed"
    assert routed["routed_to_team"] == "DATABASE"


@pytest.mark.asyncio  
async def test_user_cannot_approve_operation(client: AsyncClient):
    """Test: normal user cannot approve restricted operations"""
    # Create as admin first
    login_res = await client.post("/auth/login", json={"email": "admin@company.com", "password": "password123"})
    admin_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}
    
    cats_res = await client.get("/categories")
    cat = cats_res.json()[0]
    create_res = await client.post("/tickets", json={
        "title": "Transfer client data",
        "description": "Move data from client 100 to client 200",
        "category_id": cat["id"],
        "priority": "medium",
        "activity_code": "CLIENT_DATA_TRANSFER",
        "requires_admin_approval": True,
        "operation_status": "pending"
    }, headers=admin_headers)
    ticket_id = create_res.json()["id"]
    
    await client.patch(f"/tickets/{ticket_id}",
        json={"status": "pending_admin_approval"},
        headers=admin_headers)
    
    # User tries to approve - should fail
    user_login = await client.post("/auth/login", json={"email": "john@company.com", "password": "password123"})
    user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}
    
    approve_res = await client.post(f"/tickets/{ticket_id}/approve", headers=user_headers)
    assert approve_res.status_code in [403, 404, 422, 400]

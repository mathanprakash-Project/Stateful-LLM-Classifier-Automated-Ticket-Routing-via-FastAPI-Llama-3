"""
Tests for Chat session, AI LangGraph conversation, draft creation, out-of-scope guardrails, and human approval.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_turn_and_approval_flow(client: AsyncClient):
    # 1. Login as John Doe
    login_resp = await client.post(
        "/auth/login",
        json={"email": "john@company.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Chat Session
    session_resp = await client.post("/chat/sessions", headers=headers)
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]

    # 3. Send Turn 1: Grievance Message (triggers diagnostic clarification)
    msg1_resp = await client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "My work laptop screen keeps turning black."},
        headers=headers,
    )
    assert msg1_resp.status_code == 200
    data1 = msg1_resp.json()
    assert "response" in data1

    # 4. Send Turn 2: Diagnostic answer with affected system and troubleshooting (triggers complete draft generation)
    msg2_resp = await client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "It is a Dell Latitude 7420 running Windows 11. I already tried hard rebooting and reconnecting the HDMI cable. It happens every 10 minutes and completely blocks my work."},
        headers=headers,
    )
    assert msg2_resp.status_code == 200
    data2 = msg2_resp.json()
    assert data2["draft"] is not None
    draft = data2["draft"]
    draft_id = draft["id"]
    assert draft["status"] == "pending_review"

    # 5. User approves the draft ticket
    approve_resp = await client.post(
        f"/chat/sessions/{session_id}/drafts/{draft_id}/approve",
        headers=headers,
    )
    assert approve_resp.status_code == 200
    approval_data = approve_resp.json()
    assert "ticket_number" in approval_data
    assert approval_data["ticket_number"].startswith("TKT-")

    # 6. Verify the ticket appears in ticket list
    tickets_resp = await client.get("/tickets", headers=headers)
    assert tickets_resp.status_code == 200
    items = tickets_resp.json()["items"]
    assert any(t["ticket_number"] == approval_data["ticket_number"] for t in items)


@pytest.mark.asyncio
async def test_out_of_scope_message_rejected(client: AsyncClient):
    # 1. Login as John Doe
    login_resp = await client.post(
        "/auth/login",
        json={"email": "john@company.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Chat Session
    session_resp = await client.post("/chat/sessions", headers=headers)
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]

    # 3. Send Out-of-Scope Message (e.g. clothing inquiry)
    msg_resp = await client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "My pant is too tight from zudio cargo."},
        headers=headers,
    )
    assert msg_resp.status_code == 200
    data = msg_resp.json()
    assert data.get("draft") is None
    assert "technical IT support" in data["response"] or "cannot create support tickets" in data["response"] or "non-technical" in data["response"].lower()


@pytest.mark.asyncio
async def test_explain_single_activity_alone(client: AsyncClient):
    login_resp = await client.post(
        "/auth/login",
        json={"email": "john@company.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    session_resp = await client.post("/chat/sessions", headers=headers)
    session_id = session_resp.json()["id"]

    # Ask specifically to explain Client Data Transfer alone
    msg_resp = await client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "can u explain the activity of client transfer data alone"},
        headers=headers,
    )
    assert msg_resp.status_code == 200
    data = msg_resp.json()
    resp_text = data["response"]

    # Must contain Client Data Transfer details and NOT the full overview table of other activities
    assert "Client Data Transfer" in resp_text or "CLIENT_DATA_TRANSFER" in resp_text
    assert "User Lockout" in resp_text or "lock" in resp_text.lower()
    assert "Prerequisites Checklist" in resp_text or "Prerequisites" in resp_text
    # Ensure it did not dump the full 5-activity table
    assert "Application Versioning" not in resp_text or "Operational Property" in resp_text


@pytest.mark.asyncio
async def test_explain_hybrid_execution_mode_and_downtime(client: AsyncClient):
    login_resp = await client.post(
        "/auth/login",
        json={"email": "john@company.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    session_resp = await client.post("/chat/sessions", headers=headers)
    session_id = session_resp.json()["id"]

    # Ask the exact user query: "execution mode can you explain what is about hybrid do we need to give downtime are not"
    msg_resp = await client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "execution mode can you explain what is about hybrid do we need to give downtime are not"},
        headers=headers,
    )
    assert msg_resp.status_code == 200
    data = msg_resp.json()
    resp_text = data["response"]

    # Must explain Hybrid mode and Downtime / Lockout policy
    assert "Hybrid" in resp_text
    assert "NO Full" in resp_text or "No Full" in resp_text or "not required" in resp_text.lower()
    assert "User Lockout" in resp_text or "lock" in resp_text.lower()
    # Must NOT return the generic overview greeting table
    assert "Enterprise Application Support AI Specialist" not in resp_text


@pytest.mark.asyncio
async def test_multiturn_history_context(client: AsyncClient):
    login_resp = await client.post(
        "/auth/login",
        json={"email": "john@company.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    session_resp = await client.post("/chat/sessions", headers=headers)
    session_id = session_resp.json()["id"]

    # Turn 1: Ask about Client Data Transfer
    await client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "tell me about client data transfer"},
        headers=headers,
    )

    # Turn 2: Follow-up question about downtime
    msg2_resp = await client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "is downtime required for this?"},
        headers=headers,
    )
    assert msg2_resp.status_code == 200
    resp_text = msg2_resp.json()["response"]
    assert "Lockout" in resp_text or "downtime" in resp_text.lower()



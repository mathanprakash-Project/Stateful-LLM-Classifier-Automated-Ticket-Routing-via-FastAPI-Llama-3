import asyncio
import httpx

async def test_e2e():
    async with httpx.AsyncClient(base_url="http://ui") as client:
        # 1. Login as user (venu@company.com)
        res = await client.post("/api/auth/login", json={"email": "venu@company.com", "password": "password123"})
        assert res.status_code == 200, f"User login failed: {res.text}"
        user_token = res.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 2. Login as manager (mathan@company.com)
        res = await client.post("/api/auth/login", json={"email": "mathan@company.com", "password": "password123"})
        assert res.status_code == 200, f"Manager login failed: {res.text}"
        manager_token = res.json()["access_token"]
        manager_headers = {"Authorization": f"Bearer {manager_token}"}

        # 3. Login as admin (admin@company.com)
        res = await client.post("/api/auth/login", json={"email": "admin@company.com", "password": "password123"})
        assert res.status_code == 200, f"Admin login failed: {res.text}"
        admin_token = res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 4. Get categories
        res = await client.get("/api/categories", headers=user_headers)
        categories = res.json()
        cat_id = categories[0]["id"]

        # 5. User creates an Application UI ticket (Online, no downtime)
        res = await client.post("/api/tickets", json={
            "title": "Test UI Maintenance Button Bug",
            "description": "Customer reports submit button disabled on settings page.",
            "category_id": cat_id,
            "activity_code": "APPLICATION_UI",
            "priority": "medium",
            "execution_mode": "Online",
            "downtime_required": False,
            "prerequisites_confirmed": True,
            "downtime_acknowledged": False
        }, headers=user_headers)
        assert res.status_code == 201, f"Create ticket failed: {res.text}"
        t1 = res.json()
        t1_id = t1["id"]
        t1_num = t1["ticket_number"]
        print(f"PASS: Ticket 1 created: {t1_num} status={t1['status']}")

        # Inspect routing_details on open ticket
        assert "routing_details" in t1, "routing_details missing!"
        rd1 = t1["routing_details"]
        print(f"      Routing details: to={rd1['role_title']} | policy={rd1['routing_policy']}")

        # 6. User requests cancellation
        res = await client.post(f"/api/tickets/{t1_id}/request-cancellation", json={
            "reason": "Customer realized this was solved by browser cache clear."
        }, headers=user_headers)
        assert res.status_code == 200, f"Request cancel failed: {res.text}"
        t1_cancelling = res.json()
        assert t1_cancelling["status"] == "pending_cancellation"
        print(f"PASS: Ticket 1 requested cancellation: status={t1_cancelling['status']}")

        # Inspect routing_details when pending_cancellation
        rd_cancel = t1_cancelling["routing_details"]
        print(f"      Cancellation Routing: to={rd_cancel['role_title']} requires_approval={rd_cancel['requires_approval']}")
        assert rd_cancel["requires_approval"] == True
        assert rd_cancel["routed_to_role"] == "manager"

        # 7. Manager approves cancellation
        res = await client.post(f"/api/tickets/{t1_id}/approve-cancellation", json={
            "notes": "Verified requester self-healed issue. Cancellation approved."
        }, headers=manager_headers)
        assert res.status_code == 200, f"Approve cancel failed: {res.text}"
        t1_cancelled = res.json()
        assert t1_cancelled["status"] == "cancelled"
        print(f"PASS: Ticket 1 cancellation approved: status={t1_cancelled['status']}")

        # 8. Test Reject Cancellation: User creates Ticket 2
        res = await client.post("/api/tickets", json={
            "title": "Test File Housekeeping Request",
            "description": "Archive old audit logs to cold storage.",
            "category_id": cat_id,
            "activity_code": "FILE_MANAGEMENT",
            "priority": "medium",
            "execution_mode": "Online",
            "downtime_required": False,
            "prerequisites_confirmed": True,
            "downtime_acknowledged": False
        }, headers=user_headers)
        assert res.status_code == 201
        t2 = res.json()
        t2_id = t2["id"]
        original_status = t2["status"]
        print(f"PASS: Ticket 2 created: {t2['ticket_number']} status={original_status}")

        # User requests cancellation
        res = await client.post(f"/api/tickets/{t2_id}/request-cancellation", json={
            "reason": "Requested by mistake."
        }, headers=user_headers)
        assert res.status_code == 200
        assert res.json()["status"] == "pending_cancellation"
        print("PASS: Ticket 2 requested cancellation: pending_cancellation")

        # Manager rejects cancellation (keeps active)
        res = await client.post(f"/api/tickets/{t2_id}/reject-cancellation", json={
            "reason": "Housekeeping is mandatory under enterprise retention compliance. Restoring ticket to active queue."
        }, headers=manager_headers)
        assert res.status_code == 200
        t2_restored = res.json()
        assert t2_restored["status"] == original_status, f"Expected {original_status}, got {t2_restored['status']}"
        print(f"PASS: Ticket 2 cancellation rejected by manager: restored to {t2_restored['status']}")

        # 9. Verify Restricted Operation Routing (APPLICATION_VERSION -> Admin approval)
        res = await client.post("/api/tickets", json={
            "title": "Core Application Engine Upgrade v2.4",
            "description": "Planned maintenance upgrade to core application binaries.",
            "category_id": cat_id,
            "activity_code": "APPLICATION_VERSION",
            "priority": "critical",
            "execution_mode": "Offline",
            "downtime_required": True,
            "prerequisites_confirmed": True,
            "downtime_acknowledged": True
        }, headers=user_headers)
        assert res.status_code == 201
        t3 = res.json()
        assert t3["status"] == "pending_admin_approval"
        rd3 = t3["routing_details"]
        print(f"PASS: Ticket 3 Restricted Operation: status={t3['status']} routed_to={rd3['role_title']} policy={rd3['routing_policy']}")
        assert rd3["routed_to_role"] == "admin"
        assert rd3["requires_approval"] == True

        # 10. Verify Model Monitoring endpoint through Nginx
        res = await client.get("/api/metrics/model-monitoring")
        assert res.status_code == 200
        metrics = res.json()
        assert "tiered_router" in metrics
        assert "overview" in metrics
        assert "rag_retrieval" in metrics
        assert "rai_safety" in metrics
        assert "consensus_validation" in metrics
        print("PASS: Model Monitoring endpoint verified through Nginx (/api/metrics/model-monitoring)!")

        print("\nALL 10 END-TO-END TESTS PASSED THROUGH DOCKER COMPOSE STACK!")

if __name__ == "__main__":
    asyncio.run(test_e2e())

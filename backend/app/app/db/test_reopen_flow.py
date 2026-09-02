"""
End-to-end verification of customer reopen flow, detailed reason, and elevated priority.
"""
import asyncio
import httpx

async def test_full_reopen_flow():
    async with httpx.AsyncClient(base_url="http://localhost:8000/api") as client:
        # 1. Login user
        u_res = await client.post("/auth/login", json={"email": "venu@company.com", "password": "password123"})
        assert u_res.status_code == 200, f"User login failed: {u_res.text}"
        u_token = u_res.json()["access_token"]
        u_headers = {"Authorization": f"Bearer {u_token}"}
        
        # 2. Get category and create ticket
        cats = (await client.get("/categories", headers=u_headers)).json()
        t_res = await client.post("/tickets", json={
            "title": "E2E Reopen Priority Verification Ticket",
            "description": "Customer verifying maintenance activity on application versioning",
            "category_id": cats[0]["id"],
            "priority": "medium"
        }, headers=u_headers)
        assert t_res.status_code == 201, f"Create ticket failed: {t_res.text}"
        ticket = t_res.json()
        t_id = ticket["id"]
        print(f"Created ticket #{ticket['ticket_number']} (Initial Priority: {ticket['priority']})")
        
        # 3. Employee starts & resolves
        e_res = await client.post("/auth/login", json={"email": "eegan@company.com", "password": "password123"})
        assert e_res.status_code == 200, f"Employee login failed: {e_res.text}"
        e_token = e_res.json()["access_token"]
        e_headers = {"Authorization": f"Bearer {e_token}"}
        await client.post(f"/tickets/{t_id}/start-work", headers=e_headers)
        await client.post(f"/tickets/{t_id}/complete-work", json={"notes": "Completed initial maintenance activity"}, headers=e_headers)
        print("Employee completed and marked ticket as Resolved.")
        
        # 4. User reopens with detailed reason
        detailed_reason = "Service restarted successfully, but client data indexing failed on partition B."
        reopen_res = await client.post(f"/tickets/{t_id}/reopen", json={"reason": detailed_reason}, headers=u_headers)
        assert reopen_res.status_code == 200, f"Reopen ticket failed: {reopen_res.text}"
        reopened_ticket = reopen_res.json()
        
        print(f"Reopened Ticket Status: {reopened_ticket['status']}")
        print(f"Reopened Ticket Priority: {reopened_ticket['priority']} (Elevated)")
        print(f"Reopened Count: {reopened_ticket.get('meta_info', {}).get('reopen_count')}/3")
        print(f"Latest Reopen Reason: \"{reopened_ticket.get('meta_info', {}).get('latest_reopen_reason')}\"")
        
        assert reopened_ticket["status"] == "reopened"
        assert reopened_ticket["priority"] == "high"
        assert reopened_ticket.get("meta_info", {}).get("latest_reopen_reason") == detailed_reason
        
        # 5. Admin can assign this reopened ticket to an employee
        a_res = await client.post("/auth/login", json={"email": "adhi@company.com", "password": "password123"})
        a_token = a_res.json()["access_token"]
        a_headers = {"Authorization": f"Bearer {a_token}"}
        
        # Reopened ticket can be assigned directly to employee
        assign_res = await client.patch(f"/tickets/{t_id}", json={
            "assigned_to_id": e_res.json()["user"]["id"],
            "status": "assigned"
        }, headers=a_headers)
        assert assign_res.status_code == 200, f"Admin assign failed: {assign_res.text}"
        print(f"Admin assigned reopened ticket to employee (Status: {assign_res.json()['status']})")
        
        # 6. Employee executes and resolves again
        await client.post(f"/tickets/{t_id}/start-work", headers=e_headers)
        res_again = await client.post(f"/tickets/{t_id}/complete-work", json={"notes": "Partition B re-indexed and verified"}, headers=e_headers)
        assert res_again.status_code == 200
        print(f"Employee re-executed and resolved ticket again (Status: {res_again.json()['status']})")
        
        print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_full_reopen_flow())


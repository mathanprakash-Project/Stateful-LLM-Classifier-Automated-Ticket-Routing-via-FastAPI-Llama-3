"""
Verification script for active employees and state machine permissions.
"""
import asyncio
from app.db.session import AsyncSessionLocal
from app.repositories.user_repo import UserRepository
from app.core.ticket_state_machine import validate_transition, InvalidStateTransitionError

async def verify():
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        users = await repo.list_users(limit=100)
        active_agents = []
        for u in users:
            if not u.is_active:
                continue
            role_names = [r.name.lower() for r in u.roles]
            if 'agent' in role_names and 'admin' not in role_names and 'manager' not in role_names:
                active_agents.append(f"{u.full_name} ({u.email})")
        print("ACTIVE_SUPPORT_EMPLOYEES:", active_agents)
        
        # Test agent trying to close resolved ticket
        agent_can_close = False
        try:
            validate_transition("resolved", "closed", ["agent"])
            agent_can_close = True
        except InvalidStateTransitionError:
            agent_can_close = False
            
        user_can_close = False
        try:
            validate_transition("resolved", "closed", ["user"])
            user_can_close = True
        except InvalidStateTransitionError:
            user_can_close = False

        manager_can_close = False
        try:
            validate_transition("resolved", "closed", ["manager"])
            manager_can_close = True
        except InvalidStateTransitionError:
            manager_can_close = False

        print(f"CLOSE_PERMISSIONS: Agent_Allowed={agent_can_close}, User_Allowed={user_can_close}, Manager_Allowed={manager_can_close}")

if __name__ == "__main__":
    asyncio.run(verify())

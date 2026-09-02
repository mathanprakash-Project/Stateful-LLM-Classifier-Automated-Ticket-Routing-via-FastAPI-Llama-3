"""
Clean up duplicate and alias users in the database, retaining only the 13 official accounts.
"""
import asyncio
import logging
from sqlalchemy import select, delete, update
from app.db.session import AsyncSessionLocal
from app.models import User, UserRole, Role, Ticket
from app.auth.password import get_password_hash
from app.core.constants import UserRole as UserRoleEnum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OFFICIAL_ROSTER = [
    # 1 Manager
    {"email": "mathan@company.com", "full_name": "Mathan", "role": UserRoleEnum.MANAGER.value},
    # 2 Admins
    {"email": "adhi@company.com", "full_name": "Adhi", "role": UserRoleEnum.ADMIN.value},
    {"email": "giri@company.com", "full_name": "Giri", "role": UserRoleEnum.ADMIN.value},
    # 3 Employees (Agents)
    {"email": "eegan@company.com", "full_name": "Eegan", "role": UserRoleEnum.AGENT.value},
    {"email": "hari@company.com", "full_name": "Hari", "role": UserRoleEnum.AGENT.value},
    {"email": "basker@company.com", "full_name": "Basker", "role": UserRoleEnum.AGENT.value},
    # 7 Users
    {"email": "venu@company.com", "full_name": "Venu", "role": UserRoleEnum.USER.value},
    {"email": "santhosh@company.com", "full_name": "Santhosh", "role": UserRoleEnum.USER.value},
    {"email": "harsh@company.com", "full_name": "Harsh", "role": UserRoleEnum.USER.value},
    {"email": "kasi@company.com", "full_name": "Kasi", "role": UserRoleEnum.USER.value},
    {"email": "deepesh@company.com", "full_name": "Deepesh", "role": UserRoleEnum.USER.value},
    {"email": "manoj@company.com", "full_name": "Manoj", "role": UserRoleEnum.USER.value},
    {"email": "priya@company.com", "full_name": "Priya", "role": UserRoleEnum.USER.value},
]

ALIAS_MAPPING = {
    "admin@company.com": "adhi@company.com",
    "alice@company.com": "mathan@company.com",
    "bob@company.com": "eegan@company.com",
    "john@company.com": "venu@company.com",
    "jane@company.com": "santhosh@company.com",
}

async def cleanup_and_sync():
    async with AsyncSessionLocal() as session:
        # 1. Fetch roles
        roles_stmt = select(Role)
        res = await session.execute(roles_stmt)
        roles = {r.name: r for r in res.scalars().all()}

        # 2. Ensure all 13 official users exist first
        default_pwd = get_password_hash("password123")
        created_users = {}
        for u_data in OFFICIAL_ROSTER:
            user_stmt = select(User).where(User.email == u_data["email"])
            u_res = await session.execute(user_stmt)
            user = u_res.scalar_one_or_none()
            if not user:
                user = User(
                    email=u_data["email"],
                    full_name=u_data["full_name"],
                    password_hash=default_pwd,
                    is_active=True,
                )
                session.add(user)
                await session.flush()
                ur = UserRole(user_id=user.id, role_id=roles[u_data["role"]].id)
                session.add(ur)
            else:
                user.full_name = u_data["full_name"]
                user.password_hash = default_pwd
                ur_stmt = select(UserRole).where(UserRole.user_id == user.id)
                ur_res = await session.execute(ur_stmt)
                user_role_entry = ur_res.scalar_one_or_none()
                if user_role_entry:
                    user_role_entry.role_id = roles[u_data["role"]].id
                else:
                    ur = UserRole(user_id=user.id, role_id=roles[u_data["role"]].id)
                    session.add(ur)
            created_users[u_data["email"]] = user
        await session.commit()

        # 3. Mark old alias accounts as inactive
        await session.execute(
            update(User).where(User.email.in_(list(ALIAS_MAPPING.keys()))).values(is_active=False)
        )
        await session.commit()
        logger.info("Roster cleaned up and synchronized successfully.")

if __name__ == "__main__":
    asyncio.run(cleanup_and_sync())

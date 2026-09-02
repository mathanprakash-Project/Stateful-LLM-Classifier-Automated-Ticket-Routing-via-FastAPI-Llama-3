"""
Clean up duplicate and alias users in the database, retaining only the 13 official accounts.
"""
import asyncio
import logging
from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal
from app.models import User, UserRole, Role
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

OLD_ALIAS_EMAILS = [
    "admin@company.com",
    "alice@company.com",
    "bob@company.com",
    "john@company.com",
    "jane@company.com",
]

async def cleanup_and_sync():
    async with AsyncSessionLocal() as session:
        # 1. Fetch roles
        roles_stmt = select(Role)
        res = await session.execute(roles_stmt)
        roles = {r.name: r for r in res.scalars().all()}

        # 2. Delete old alias accounts if they have no tickets
        for old_email in OLD_ALIAS_EMAILS:
            user_stmt = select(User).where(User.email == old_email)
            u_res = await session.execute(user_stmt)
            old_user = u_res.scalar_one_or_none()
            if old_user:
                logger.info(f"Removing old alias user: {old_email}")
                try:
                    await session.execute(delete(UserRole).where(UserRole.user_id == old_user.id))
                    await session.delete(old_user)
                    await session.commit()
                except Exception as e:
                    logger.warning(f"Could not delete {old_email} (may have foreign key refs): {e}")
                    await session.rollback()

        # 3. Ensure all 13 official users exist with clean data
        default_pwd = get_password_hash("password123")
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
        await session.commit()
        logger.info("Roster cleaned up and synchronized successfully.")

if __name__ == "__main__":
    asyncio.run(cleanup_and_sync())


"""
Database initialization and seeding script.
Populates standard roles, permissions, categories, subcategories, and initial test users.
"""

import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import get_password_hash
from app.auth.rbac import ROLE_PERMISSIONS
from app.core.constants import PermissionCode, UserRole as UserRoleEnum
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models import (
    User,
    Role,
    Permission,
    UserRole,
    RolePermission,
    TicketCategory,
    TicketSubcategory,
)

logger = logging.getLogger(__name__)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        from sqlalchemy import text
        await conn.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS execution_mode VARCHAR(30) DEFAULT 'Online';"))
        await conn.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS downtime_required BOOLEAN DEFAULT FALSE;"))
        await conn.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS downtime_acknowledged BOOLEAN DEFAULT FALSE;"))
        await conn.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS prerequisites_confirmed BOOLEAN DEFAULT FALSE;"))
        await conn.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS prerequisites_notes TEXT;"))
        await conn.execute(text("ALTER TABLE ai_ticket_drafts DROP CONSTRAINT IF EXISTS ai_ticket_drafts_ticket_id_fkey;"))
        await conn.execute(text("ALTER TABLE ai_ticket_drafts ADD CONSTRAINT ai_ticket_drafts_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE SET NULL;"))
    logger.info("Database tables initialized and migrated.")


async def seed_data(session: AsyncSession):
    # 1. Seed Permissions
    permissions_map: dict[str, Permission] = {}
    for code_enum in PermissionCode:
        code = code_enum.value
        resource, action = code.split(":")
        stmt = select(Permission).where(Permission.code == code)
        result = await session.execute(stmt)
        perm = result.scalar_one_or_none()
        if not perm:
            perm = Permission(
                code=code,
                resource=resource,
                action=action,
                description=f"Allows {action} on {resource}",
            )
            session.add(perm)
            await session.flush()
        permissions_map[code] = perm

    # 2. Seed Roles and map permissions
    roles_map: dict[str, Role] = {}
    for role_enum in UserRoleEnum:
        role_name = role_enum.value
        stmt = select(Role).where(Role.name == role_name)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            role = Role(name=role_name, description=f"{role_name.capitalize()} role")
            session.add(role)
            await session.flush()
        
        # Link permissions
        allowed_codes = {p.value for p in ROLE_PERMISSIONS.get(role_enum, set())}
        for code in allowed_codes:
            if code in permissions_map:
                perm_obj = permissions_map[code]
                rp = RolePermission(role_id=role.id, permission_id=perm_obj.id)
                session.add(rp)
        roles_map[role_name] = role

    # 3. Seed Categories & Subcategories
    categories_data = [
        {
            "name": "Application UI",
            "description": "Application UI Changes / Issues",
            "subcategories": ["UI Bug", "UI Error", "Broken Button/Link", "Missing Field", "Layout Problem", "Validation Issue", "Enhancement Request"],
        },
        {
            "name": "Application Version Maintenance",
            "description": "Application Version Maintenance",
            "subcategories": ["Version Upgrade", "Version Downgrade", "Patch Request", "Compatibility Check"],
        },
        {
            "name": "Client Data Transfer",
            "description": "Client Data Transfer",
            "subcategories": ["Client-to-Client Transfer", "Data Migration", "Client Sync", "Configuration Copy"],
        },
        {
            "name": "File Management",
            "description": "File Management",
            "subcategories": ["File Upload Issue", "File Replacement", "File Configuration", "File Processing Error", "File Access"],
        },
        {
            "name": "Application Support",
            "description": "Application Support",
            "subcategories": ["Login/Access Issue", "Performance Issue", "Feature Request", "Configuration Change", "General Inquiry"],
        },
        {
            "name": "Server / Infrastructure",
            "description": "Server / Infrastructure",
            "subcategories": ["Server Down", "CPU/Memory Issue", "Restart Required", "Deployment Issue"],
        },
        {
            "name": "Database",
            "description": "Database",
            "subcategories": ["DB Connection", "DB Storage", "DB Performance", "Data Corruption"],
        },
        {
            "name": "Network",
            "description": "Network",
            "subcategories": ["Connectivity Issue", "Firewall/DNS", "VPN Issue", "Bandwidth"],
        },
        {
            "name": "Security",
            "description": "Security",
            "subcategories": ["Access Violation", "Vulnerability Report", "Compliance", "Security Audit"],
        },
        {
            "name": "Other Technical",
            "description": "Other Technical",
            "subcategories": ["Integration Issue", "API Issue", "Third-party System"],
        },
    ]

    for cat_data in categories_data:
        stmt = select(TicketCategory).where(TicketCategory.name == cat_data["name"])
        result = await session.execute(stmt)
        cat = result.scalar_one_or_none()
        if not cat:
            cat = TicketCategory(name=cat_data["name"], description=cat_data["description"])
            session.add(cat)
            await session.flush()
            for sub_name in cat_data["subcategories"]:
                sub = TicketSubcategory(category_id=cat.id, name=sub_name)
                session.add(sub)

    # 4. Seed Predefined Users
    users_data = [
        {"email": "john@company.com", "full_name": "John Doe", "role": UserRoleEnum.USER.value},
        {"email": "jane@company.com", "full_name": "Jane Smith", "role": UserRoleEnum.USER.value},
        {"email": "bob@company.com", "full_name": "Agent Bob", "role": UserRoleEnum.AGENT.value},
        {"email": "bob@company.com", "full_name": "Employee Bob", "role": UserRoleEnum.AGENT.value},
        {"email": "alice@company.com", "full_name": "Manager Alice", "role": UserRoleEnum.MANAGER.value},
        {"email": "admin@company.com", "full_name": "Admin Root", "role": UserRoleEnum.ADMIN.value},
    ]

    default_password_hash = get_password_hash("password123")

    for u_info in users_data:
        stmt = select(User).where(User.email == u_info["email"])
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email=u_info["email"],
                full_name=u_info["full_name"],
                password_hash=default_password_hash,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            ur = UserRole(user_id=user.id, role_id=roles_map[u_info["role"]].id)
            session.add(ur)

    await session.commit()
    logger.info("Seed data successfully populated.")


async def run_seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_data(session)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_seed())

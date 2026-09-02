"""
Database initialization and seeding script.
Populates standard roles, permissions, categories, subcategories, and initial test users.
"""

import asyncio
import logging
from sqlalchemy import select, update, delete
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
    Ticket,
)

logger = logging.getLogger(__name__)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        from sqlalchemy import text
        migrations = [
            "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS execution_mode VARCHAR(30) DEFAULT 'Online';",
            "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS downtime_required BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS downtime_acknowledged BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS prerequisites_confirmed BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS prerequisites_notes TEXT;",
            "ALTER TABLE ai_ticket_drafts DROP CONSTRAINT IF EXISTS ai_ticket_drafts_ticket_id_fkey;",
            "ALTER TABLE ai_ticket_drafts ADD CONSTRAINT ai_ticket_drafts_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE SET NULL;",
        ]
        for mig in migrations:
            try:
                await conn.execute(text(mig))
            except Exception:
                pass
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

    # 3. Seed Categories & Subcategories (Strictly Application Activities)
    categories_data = [
        {
            "name": "Application UI",
            "description": "Application UI Changes / Issues (Online · No Downtime)",
            "subcategories": ["UI Bug", "UI Error", "Broken Button/Link", "Missing Field", "Layout Problem", "Validation Issue", "Enhancement Request"],
        },
        {
            "name": "Application Version Maintenance",
            "description": "Application Version Maintenance (Offline · Planned Downtime · Admin Approved)",
            "subcategories": ["Version Upgrade", "Version Downgrade", "Patch Request", "Compatibility Check"],
        },
        {
            "name": "Client Data Transfer",
            "description": "Client Data Transfer (Hybrid · User Lockout · Admin Approved)",
            "subcategories": ["Client-to-Client Transfer", "Data Migration", "Client Sync", "Configuration Copy"],
        },
        {
            "name": "File Management",
            "description": "File Management (Online · No Downtime)",
            "subcategories": ["File Upload Issue", "File Replacement", "File Configuration", "File Processing Error", "File Access"],
        },
    ]

    # Create/Get default Application UI category for reassignments
    stmt_ui = select(TicketCategory).where(TicketCategory.name == "Application UI")
    res_ui = await session.execute(stmt_ui)
    app_ui_cat = res_ui.scalar_one_or_none()
    if not app_ui_cat:
        app_ui_cat = TicketCategory(name="Application UI", description="Application UI Changes / Issues (Online · No Downtime)")
        session.add(app_ui_cat)
        await session.flush()

    # Clean up non-application categories
    non_app_cat_names = [
        "Server / Infrastructure", "Database", "Network", "Security", "Other Technical", "Application Support", "General Support"
    ]
    for old_name in non_app_cat_names:
        old_stmt = select(TicketCategory).where(TicketCategory.name == old_name)
        old_res = await session.execute(old_stmt)
        old_cat = old_res.scalar_one_or_none()
        if old_cat:
            # Reassign any tickets referencing this old category
            await session.execute(
                update(Ticket).where(Ticket.category_id == old_cat.id).values(category_id=app_ui_cat.id)
            )
            # Delete subcategories then category
            await session.execute(
                delete(TicketSubcategory).where(TicketSubcategory.category_id == old_cat.id)
            )
            await session.delete(old_cat)

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
        # 1 Manager
        {"email": "mathan@company.com", "full_name": "Mathan", "role": UserRoleEnum.MANAGER.value},
        {"email": "alice@company.com", "full_name": "Mathan", "role": UserRoleEnum.MANAGER.value},
        # 2 Admins
        {"email": "adhi@company.com", "full_name": "Adhi", "role": UserRoleEnum.ADMIN.value},
        {"email": "admin@company.com", "full_name": "Adhi", "role": UserRoleEnum.ADMIN.value},
        {"email": "giri@company.com", "full_name": "Giri", "role": UserRoleEnum.ADMIN.value},
        # 3 Employees
        {"email": "eegan@company.com", "full_name": "Eegan", "role": UserRoleEnum.AGENT.value},
        {"email": "bob@company.com", "full_name": "Eegan", "role": UserRoleEnum.AGENT.value},
        {"email": "hari@company.com", "full_name": "Hari", "role": UserRoleEnum.AGENT.value},
        {"email": "basker@company.com", "full_name": "Basker", "role": UserRoleEnum.AGENT.value},
        # 7 Users
        {"email": "venu@company.com", "full_name": "Venu", "role": UserRoleEnum.USER.value},
        {"email": "john@company.com", "full_name": "Venu", "role": UserRoleEnum.USER.value},
        {"email": "santhosh@company.com", "full_name": "Santhosh", "role": UserRoleEnum.USER.value},
        {"email": "jane@company.com", "full_name": "Santhosh", "role": UserRoleEnum.USER.value},
        {"email": "harsh@company.com", "full_name": "Harsh", "role": UserRoleEnum.USER.value},
        {"email": "kasi@company.com", "full_name": "Kasi", "role": UserRoleEnum.USER.value},
        {"email": "deepesh@company.com", "full_name": "Deepesh", "role": UserRoleEnum.USER.value},
        {"email": "manoj@company.com", "full_name": "Manoj", "role": UserRoleEnum.USER.value},
        {"email": "priya@company.com", "full_name": "Priya", "role": UserRoleEnum.USER.value},
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
        else:
            # Update existing user's display name
            user.full_name = u_info["full_name"]
            user.password_hash = default_password_hash
            session.add(user)

    await session.commit()
    logger.info("Seed data successfully populated.")


async def run_seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_data(session)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_seed())


"""
User and Role repository.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, Role, Permission, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.email == email.lower())
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(self, skip: int = 0, limit: int = 50) -> List[User]:
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_user(self, email: str, full_name: str, password_hash: str, role_names: List[str]) -> User:
        user = User(
            email=email.lower(),
            full_name=full_name,
            password_hash=password_hash,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()

        for r_name in role_names:
            stmt = select(Role).where(Role.name == r_name.lower())
            res = await self.db.execute(stmt)
            role = res.scalar_one_or_none()
            if role:
                ur = UserRole(user_id=user.id, role_id=role.id)
                self.db.add(ur)

        await self.db.commit()
        return await self.get_by_id(user.id)


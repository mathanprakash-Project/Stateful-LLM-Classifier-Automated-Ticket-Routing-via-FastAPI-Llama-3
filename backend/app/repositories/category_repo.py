"""
Category and Subcategory repository.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import TicketCategory, TicketSubcategory


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, active_only: bool = True) -> List[TicketCategory]:
        stmt = select(TicketCategory).options(selectinload(TicketCategory.subcategories))
        if active_only:
            stmt = stmt.where(TicketCategory.is_active == True)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, category_id: str) -> Optional[TicketCategory]:
        stmt = (
            select(TicketCategory)
            .where(TicketCategory.id == category_id)
            .options(selectinload(TicketCategory.subcategories))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[TicketCategory]:
        stmt = (
            select(TicketCategory)
            .where(TicketCategory.name.ilike(name.strip()))
            .options(selectinload(TicketCategory.subcategories))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_subcategory_by_id(self, subcategory_id: str) -> Optional[TicketSubcategory]:
        stmt = select(TicketSubcategory).where(TicketSubcategory.id == subcategory_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_subcategory_by_name(self, category_id: str, name: str) -> Optional[TicketSubcategory]:
        stmt = (
            select(TicketSubcategory)
            .where(TicketSubcategory.category_id == category_id, TicketSubcategory.name.ilike(name.strip()))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


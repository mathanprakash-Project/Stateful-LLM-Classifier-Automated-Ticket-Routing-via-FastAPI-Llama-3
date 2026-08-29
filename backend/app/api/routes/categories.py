"""
Category and subcategory endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.repositories.category_repo import CategoryRepository
from app.schemas.category import CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    repo = CategoryRepository(db)
    return await repo.list_all(active_only=True)


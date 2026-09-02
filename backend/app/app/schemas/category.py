"""
Category and Subcategory schemas.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SubcategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category_id: str
    name: str
    is_active: bool


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    subcategories: List[SubcategoryResponse] = []


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SubcategoryCreate(BaseModel):
    name: str


"""
User management endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserSummary

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserSummary])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    users = await repo.list_users(limit=100)
    return [
        UserSummary(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            roles=[r.name for r in u.roles],
        )
        for u in users
    ]


@router.get("/agents")
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    users = await repo.list_users(limit=100)
    agents = []
    for u in users:
        role_names = [r.name.lower() for r in u.roles]
        if "agent" in role_names or "admin" in role_names or "manager" in role_names:
            agents.append({
                "id": u.id,
                "email": u.email,
                "name": f"{u.full_name} ({', '.join(r.upper() for r in role_names)})",
                "roles": role_names,
            })
    return agents


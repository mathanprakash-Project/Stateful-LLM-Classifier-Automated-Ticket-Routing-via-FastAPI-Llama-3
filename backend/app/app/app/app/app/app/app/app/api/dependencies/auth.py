"""
Authentication and RBAC FastAPI dependencies.
"""

from typing import List, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.jwt_handler import decode_token
from app.auth.rbac import has_permission
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.db.session import get_db
from app.models import User, Role, Permission

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_TOKEN", "message": "Authentication token is required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Token missing subject")
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": exc.code, "message": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = (
        select(User)
        .where(User.id == user_id, User.is_active == True)
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "User not found or inactive"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(*required_roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_names = [r.name.lower() for r in current_user.roles]
        # Admin can access anything
        if "admin" in user_role_names:
            return current_user
        
        has_any_role = any(req.lower() in user_role_names for req in required_roles)
        if not has_any_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": f"Requires one of roles: {list(required_roles)}"},
            )
        return current_user

    return role_checker


def require_permission(required_permission: str):
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_names = [r.name.lower() for r in current_user.roles]
        if "admin" in user_role_names:
            return current_user

        # Collect user permissions
        user_perms: set[str] = set()
        for role in current_user.roles:
            for perm in role.permissions:
                user_perms.add(perm.code)

        if required_permission not in user_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": f"Requires permission: {required_permission}"},
            )
        return current_user

    return permission_checker


"""
Authentication and user service.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from app.auth.password import verify_password
from app.auth.rbac import get_permissions_for_roles
from app.config.settings import settings
from app.core.exceptions import AuthenticationError, NotFoundError
from app.models import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, TokenRefreshResponse, TokenResponse, UserResponse, UserSummary


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def authenticate(self, login_req: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(login_req.email)
        if not user:
            raise AuthenticationError("Invalid email or password.")
        
        if not verify_password(login_req.password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError("Account is inactive.")

        role_names = [r.name for r in user.roles]
        access_token = create_access_token(subject=user.id, roles=role_names)
        refresh_token = create_refresh_token(subject=user.id)

        user_summary = UserSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            roles=role_names,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_summary,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenRefreshResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type. Refresh token required.")

        user_id = payload.get("sub")
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive.")

        role_names = [r.name for r in user.roles]
        access_token = create_access_token(subject=user.id, roles=role_names)

        return TokenRefreshResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def get_user_profile(self, user: User) -> UserResponse:
        role_names = [r.name for r in user.roles]
        permissions = list(get_permissions_for_roles(role_names))
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            roles=role_names,
            permissions=permissions,
        )


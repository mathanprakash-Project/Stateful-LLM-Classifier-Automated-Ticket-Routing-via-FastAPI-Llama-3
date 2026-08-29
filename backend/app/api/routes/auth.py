"""
Authentication routes: login, refresh, profile, logout.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenRefreshResponse, TokenResponse, UserResponse
from app.schemas.common import SuccessMessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.authenticate(login_data)


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(req.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    return await auth_service.get_user_profile(current_user)


@router.post("/logout", response_model=SuccessMessageResponse)
async def logout(current_user: User = Depends(get_current_user)):
    return SuccessMessageResponse(message="Successfully logged out.")


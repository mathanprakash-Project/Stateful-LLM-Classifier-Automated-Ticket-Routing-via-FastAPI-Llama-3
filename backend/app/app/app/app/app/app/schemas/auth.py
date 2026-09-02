"""
Authentication and User Pydantic schemas.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    roles: List[str] = []

    @field_validator("roles", mode="before")
    @classmethod
    def convert_roles(cls, v: Any) -> List[str]:
        if not v:
            return []
        res = []
        for item in v:
            if hasattr(item, "name"):
                res.append(item.name)
            elif isinstance(item, str):
                res.append(item)
            else:
                res.append(str(item))
        return res


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    is_active: bool
    roles: List[str] = []
    permissions: List[str] = []

    @field_validator("roles", mode="before")
    @classmethod
    def convert_roles(cls, v: Any) -> List[str]:
        if not v:
            return []
        res = []
        for item in v:
            if hasattr(item, "name"):
                res.append(item.name)
            elif isinstance(item, str):
                res.append(item)
            else:
                res.append(str(item))
        return res


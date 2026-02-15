from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models import UserRole


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    id: UUID
    email: str
    role: UserRole
    is_active: bool
    auth_provider: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleLoginResponse(BaseModel):
    authorization_url: str
    state: str

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import get_current_user
from app.db.models import User
from app.db.session import get_async_session
from app.schemas.auth import (
    GoogleLoginResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from app.services.auth_service import AuthService, AuthServiceError

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    return AuthService(session=session)


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        return await auth_service.register(payload.email, payload.password)
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": exc.message}) from exc


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        return await auth_service.login(payload.email, payload.password)
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": exc.message}) from exc


@router.get("/me", response_model=UserPublic)
async def me(current_user: User = Depends(get_current_user)):
    return UserPublic.model_validate(current_user)


@router.get("/google/login", response_model=GoogleLoginResponse)
async def google_login(auth_service: AuthService = Depends(get_auth_service)):
    try:
        return auth_service.google_login()
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": exc.message}) from exc


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(
    code: str = Query(..., description="Google authorization code"),
    state: str | None = Query(default=None, description="Google OAuth state"),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        return await auth_service.google_callback(code=code, state=state)
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": exc.message}) from exc

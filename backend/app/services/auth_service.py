from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.google_oauth import (
    build_google_authorization_url,
    exchange_authorization_code,
    verify_google_id_token,
)
from app.auth.security import (
    create_access_token,
    create_google_oauth_state,
    hash_password,
    verify_google_oauth_state,
    verify_password,
)
from app.config import get_settings
from app.db.models import User, UserRole
from app.schemas.auth import GoogleLoginResponse, TokenResponse, UserPublic


class AuthServiceError(Exception):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    async def _find_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == self._normalize_email(email))
        )
        return result.scalar_one_or_none()

    async def register(self, email: str, password: str) -> UserPublic:
        normalized_email = self._normalize_email(email)

        existing = await self._find_user_by_email(normalized_email)
        if existing is not None:
            raise AuthServiceError("Email is already registered", 409)

        user = User(
            email=normalized_email,
            hashed_password=hash_password(password),
            role=UserRole.IMPORTER,
            is_active=True,
            auth_provider="local",
        )

        self.session.add(user)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AuthServiceError("Email is already registered", 409) from exc

        await self.session.refresh(user)
        return UserPublic.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self._find_user_by_email(email)

        if user is None or user.hashed_password is None:
            raise AuthServiceError("Invalid email or password", 401)

        if not verify_password(password, user.hashed_password):
            raise AuthServiceError("Invalid email or password", 401)

        if not user.is_active:
            raise AuthServiceError("User account is inactive", 403)

        access_token = create_access_token(user)
        return TokenResponse(access_token=access_token)

    def google_login(self) -> GoogleLoginResponse:
        state = create_google_oauth_state()

        try:
            auth_url = build_google_authorization_url(self.settings, state)
        except ValueError as exc:
            raise AuthServiceError(str(exc), 503) from exc

        return GoogleLoginResponse(authorization_url=auth_url, state=state)

    async def google_callback(self, code: str, state: str | None) -> TokenResponse:
        if not state:
            raise AuthServiceError("OAuth state is required", 400)

        try:
            verify_google_oauth_state(state)
        except ValueError as exc:
            raise AuthServiceError(str(exc), 400) from exc

        try:
            token_payload = await exchange_authorization_code(self.settings, code)
        except ValueError as exc:
            raise AuthServiceError(str(exc), 400) from exc

        id_token = token_payload.get("id_token")
        if not id_token:
            raise AuthServiceError("Google token response missing id_token", 400)

        try:
            claims = await verify_google_id_token(
                id_token, audience=self.settings.google_client_id or ""
            )
        except ValueError as exc:
            raise AuthServiceError(str(exc), 401) from exc

        email = self._normalize_email(claims["email"])
        google_sub = claims["sub"]

        result = await self.session.execute(
            select(User).where(or_(User.google_sub == google_sub, User.email == email))
        )
        user = result.scalar_one_or_none()

        if user is not None:
            if not user.is_active:
                raise AuthServiceError("User account is inactive", 403)

            user.google_sub = google_sub
            user.auth_provider = "google"
        else:
            user = User(
                email=email,
                hashed_password=None,
                role=UserRole.IMPORTER,
                is_active=True,
                auth_provider="google",
                google_sub=google_sub,
            )
            self.session.add(user)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AuthServiceError("Unable to complete Google login", 409) from exc

        await self.session.refresh(user)
        access_token = create_access_token(user)
        return TokenResponse(access_token=access_token)

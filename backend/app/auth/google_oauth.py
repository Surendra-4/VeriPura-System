import asyncio
import re
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt

from app.config import Settings

GOOGLE_OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_OAUTH_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")


class GoogleJWKSCache:
    """In-memory JWKS cache to avoid key fetches on every callback."""

    _jwks: dict | None = None
    _expires_at: datetime | None = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_jwks(cls) -> dict:
        now = datetime.now(UTC)

        if cls._jwks is not None and cls._expires_at is not None and now < cls._expires_at:
            return cls._jwks

        async with cls._lock:
            now = datetime.now(UTC)
            if cls._jwks is not None and cls._expires_at is not None and now < cls._expires_at:
                return cls._jwks

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(GOOGLE_OAUTH_JWKS_URL)
                response.raise_for_status()

            jwks = response.json()
            if not isinstance(jwks, dict) or "keys" not in jwks:
                raise ValueError("Invalid JWKS response from Google")

            ttl_seconds = _extract_max_age_seconds(response.headers.get("cache-control", ""))
            cls._jwks = jwks
            cls._expires_at = now + timedelta(seconds=ttl_seconds)
            return jwks


def _extract_max_age_seconds(cache_control: str) -> int:
    match = re.search(r"max-age=(\d+)", cache_control)
    if not match:
        return 3600

    try:
        return max(int(match.group(1)), 60)
    except ValueError:
        return 3600


def build_google_authorization_url(settings: Settings, state: str) -> str:
    if not settings.google_oauth_enabled:
        raise ValueError("Google OAuth is not configured")

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "include_granted_scopes": "true",
        "state": state,
        "prompt": "select_account",
    }

    return f"{GOOGLE_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_authorization_code(settings: Settings, code: str) -> dict:
    if not settings.google_oauth_enabled:
        raise ValueError("Google OAuth is not configured")

    payload = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            GOOGLE_OAUTH_TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code >= 400:
        raise ValueError("Google token exchange failed")

    data = response.json()
    if "id_token" not in data:
        raise ValueError("Google token response missing id_token")

    return data


async def verify_google_id_token(id_token: str, audience: str) -> dict:
    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError as exc:
        raise ValueError("Invalid Google id_token header") from exc

    kid = header.get("kid")
    if not kid:
        raise ValueError("Google id_token missing key id")

    jwks = await GoogleJWKSCache.get_jwks()
    key_data = next((key for key in jwks["keys"] if key.get("kid") == kid), None)

    if key_data is None:
        raise ValueError("Google signing key not found")

    try:
        claims = jwt.decode(
            id_token,
            key_data,
            algorithms=["RS256"],
            audience=audience,
            options={"verify_at_hash": False},
        )
    except JWTError as exc:
        raise ValueError("Google id_token verification failed") from exc

    email = claims.get("email")
    subject = claims.get("sub")

    if not email or not subject:
        raise ValueError("Google id_token missing required claims")

    if claims.get("email_verified") is False:
        raise ValueError("Google account email is not verified")

    issuer = claims.get("iss")
    if issuer not in GOOGLE_ISSUERS:
        raise ValueError("Google id_token issuer is invalid")

    return claims

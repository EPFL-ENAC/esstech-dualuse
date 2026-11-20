import secrets
from urllib.parse import urlencode
from uuid import UUID

import httpx
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.config import config
from api.models import AuthIdentity, LearningIdentity, User
from api.models.base import utc_now
from api.models.enums import AuthProvider
from api.services.errors import NotConfiguredError, UpstreamAuthError, ValidationError
from api.services.persistence import insert_once

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

AUTH_SESSION_COOKIE = "auth_session"
OAUTH_STATE_COOKIE = "oauth_state"

# PLACEHOLDER retention value, not a decided policy: Fase 2
# (privacy/retention) has not been written yet. Revisit once it has.
SESSION_COOKIE_MAX_AGE = 30 * 24 * 3600
STATE_COOKIE_MAX_AGE = 600


def google_oauth_configured() -> bool:
    """Whether this environment has real Google OAuth credentials.

    False on a dev-branch deploy before the credentials are provisioned in
    Infisical. Checks truthiness, not `is not None`: e2e disables OAuth by
    setting both to "" (unsetting them would not override the developer's
    .env), and an empty env var parses to "", never None.
    """

    return bool(config.GOOGLE_CLIENT_ID) and bool(config.GOOGLE_CLIENT_SECRET)


def _session_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(config.SECRET_KEY, salt="auth-session")


def _state_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(config.SECRET_KEY, salt="oauth-state")


def sign_session(user_id: UUID) -> str:
    """Sign a session cookie value for `user_id`."""

    return _session_serializer().dumps({"user_id": str(user_id)})


def verify_session_cookie(raw_cookie: str) -> UUID | None:
    """Verify and decode a session cookie. None if invalid, tampered, or expired."""

    try:
        payload = _session_serializer().loads(
            raw_cookie, max_age=SESSION_COOKIE_MAX_AGE
        )
    except (BadSignature, SignatureExpired):
        return None
    try:
        return UUID(payload["user_id"])
    except (KeyError, ValueError, TypeError):
        return None


def sign_state(state: str) -> str:
    """Sign a CSRF state value for the short-lived state cookie."""

    return _state_serializer().dumps(state)


def verify_state(cookie_value: str, *, query_state: str) -> bool:
    """Verify the state cookie's signature and age, and that it matches
    the state Google echoed back in the callback's query string."""

    try:
        signed_state = _state_serializer().loads(
            cookie_value, max_age=STATE_COOKIE_MAX_AGE
        )
    except (BadSignature, SignatureExpired):
        return False
    return secrets.compare_digest(signed_state, query_state)


class GoogleAuthorizeUrl(BaseModel):
    """The URL to redirect to, and the state value the caller must cookie."""

    url: str
    state: str


def build_google_authorize_url() -> GoogleAuthorizeUrl:
    """Build Google's OAuth consent-screen URL and a fresh CSRF state.

    No access_type=offline: only identity at login is needed, so no
    refresh token is requested.
    """

    if not google_oauth_configured():
        raise NotConfiguredError("Google sign-in is not configured in this environment")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    return GoogleAuthorizeUrl(
        url=f"{GOOGLE_AUTHORIZE_URL}?{urlencode(params)}", state=state
    )


class GoogleTokenResponse(BaseModel):
    """The one field this codebase actually reads from Google's token response."""

    access_token: str


class GoogleUserInfo(BaseModel):
    """Google's userinfo response.

    email_verified is captured but deliberately gates nothing: `sub` is
    the only identity key trusted.
    """

    sub: str
    email: str
    email_verified: bool


async def exchange_google_code(code: str) -> GoogleUserInfo:
    """Exchange an authorization code for Google's verified identity.

    The only network call to Google, so tests monkeypatch this. Identity
    comes from the UserInfo endpoint rather than verifying the ID token's
    JWT against Google's rotating JWKS keys locally, which would need a
    JWT/JWKS library this project doesn't have.
    """

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "redirect_uri": config.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_response.raise_for_status()
        token = GoogleTokenResponse.model_validate(token_response.json())

        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token.access_token}"},
        )
        userinfo_response.raise_for_status()
        return GoogleUserInfo.model_validate(userinfo_response.json())


async def find_auth_identity(
    session: AsyncSession, *, provider: AuthProvider, provider_subject: str
) -> AuthIdentity | None:
    return (
        await session.exec(
            select(AuthIdentity).where(
                AuthIdentity.provider == provider,
                AuthIdentity.provider_subject == provider_subject,
            )
        )
    ).first()


async def find_learning_identity(
    session: AsyncSession, *, user_id: UUID
) -> LearningIdentity | None:
    return (
        await session.exec(
            select(LearningIdentity).where(LearningIdentity.user_id == user_id)
        )
    ).first()


async def handle_google_callback(
    session: AsyncSession, *, code: str, state: str, state_cookie: str | None
) -> UUID:
    """Verify state, exchange the code, and return the user_id to sign
    into the session cookie."""

    if not google_oauth_configured():
        raise NotConfiguredError("Google sign-in is not configured in this environment")

    if state_cookie is None or not verify_state(state_cookie, query_state=state):
        raise ValidationError("Invalid or expired OAuth state")

    try:
        google_user = await exchange_google_code(code)
    except (httpx.HTTPStatusError, httpx.RequestError, PydanticValidationError) as exc:
        # Google rejected the request (e.g. a reused or expired code), was
        # unreachable, or answered with an unexpected shape: in every case
        # the identity provider failed, not the caller.
        raise UpstreamAuthError(
            "Google sign-in could not be completed. Please try again."
        ) from exc

    existing = await find_auth_identity(
        session, provider=AuthProvider.GOOGLE, provider_subject=google_user.sub
    )
    if existing is not None:
        existing.last_login_at = utc_now()
        session.add(existing)
        await session.commit()
        return existing.user_id

    # First login: one transaction, so an identity is never left partially
    # created. A concurrent first login for the same `sub` wins the UNIQUE
    # constraint, and this one signs in as the user it created.
    user = User()
    session.add(user)
    await session.flush()
    user_id = user.id

    identity, created = await insert_once(
        session,
        AuthIdentity(
            user_id=user_id,
            provider=AuthProvider.GOOGLE,
            provider_subject=google_user.sub,
            verified_email=google_user.email,
        ),
        lambda: find_auth_identity(
            session, provider=AuthProvider.GOOGLE, provider_subject=google_user.sub
        ),
    )
    if not created:
        return identity.user_id

    session.add(LearningIdentity(user_id=user_id))
    await session.commit()
    return user_id

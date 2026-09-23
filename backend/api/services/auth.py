import secrets
from datetime import datetime, timezone
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
from api.models.enums import AuthProvider
from api.services.errors import NotConfiguredError, UpstreamAuthError, ValidationError

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

AUTH_SESSION_COOKIE = "auth_session"
OAUTH_STATE_COOKIE = "oauth_state"

# PLACEHOLDER retention value, not a decided policy: Fase 2
# (privacy/retention) has not been written yet. Revisit once it has.
SESSION_COOKIE_MAX_AGE = 30 * 24 * 3600
STATE_COOKIE_MAX_AGE = 600


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def cookies_are_secure() -> bool:
    """Whether cookies should carry the Secure attribute.

    Derived from config.APP_URL's scheme -- the same signal CORS
    (api/main.py) already keys off -- rather than a new environment
    flag: http://localhost locally, https:// on any real deployment.
    """

    return config.APP_URL.startswith("https://")


def google_oauth_configured() -> bool:
    """Whether this environment has real Google OAuth credentials.

    False on a dev-branch deploy before GOOGLE_CLIENT_ID/
    GOOGLE_CLIENT_SECRET are provisioned in Infisical. The routes stay
    registered (api/main.py includes auth_router unconditionally) but
    dormant: build_google_authorize_url and handle_google_callback both
    check this first and raise NotConfiguredError rather than reaching
    config.GOOGLE_CLIENT_ID/SECRET while they're None.
    """

    return (
        config.GOOGLE_CLIENT_ID is not None and config.GOOGLE_CLIENT_SECRET is not None
    )


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

    No access_type=offline: this flow only needs identity at login time,
    not ongoing access to Google APIs afterward, so no refresh token is
    requested.
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
    """Google's userinfo response, validated like every other external
    boundary in this codebase (TagSubmission, PredictionEntry, every
    other request body) -- never read as a raw dict.

    email_verified is captured but deliberately not used to gate
    anything: provider_subject is the only identity key this codebase
    ever trusts (see AuthIdentity's docstring, api/models/auth.py). The
    email is stored as Google reports it regardless of this flag.
    """

    sub: str
    email: str
    email_verified: bool


async def exchange_google_code(code: str) -> GoogleUserInfo:
    """Exchange an authorization code for Google's verified identity.

    The only function in this module that talks to Google over the
    network -- kept as its own small function so tests can replace it
    with monkeypatch.setattr, the same seam-replacement idea
    app_client's fixture already applies to get_db_session/
    get_current_learner for the rest of this suite (tests/conftest.py).

    Verifies identity via Google's UserInfo endpoint (a second
    authenticated call using the access_token just obtained) rather than
    checking the ID token's JWT signature locally against Google's
    rotating JWKS keys: the latter needs a real JWT+JWKS library this
    project doesn't have, and hand-rolling signature verification is
    exactly the kind of risk to avoid in this module.
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
    """Verify state, exchange the code, and resolve to a real user_id.

    Returns the user_id to sign into the session cookie -- the view
    layer owns setting the cookie and redirecting, this function owns
    the identity decision, the same service/view split as everywhere
    else in this codebase (services stay free of FastAPI response
    types).

    Wraps exchange_google_code's call, not its own body: a monkeypatched
    replacement in tests can raise any of these three directly to
    exercise this exact conversion, rather than needing to reimplement
    it itself.
    """

    if not google_oauth_configured():
        raise NotConfiguredError("Google sign-in is not configured in this environment")

    if state_cookie is None or not verify_state(state_cookie, query_state=state):
        raise ValidationError("Invalid or expired OAuth state")

    try:
        google_user = await exchange_google_code(code)
    except (httpx.HTTPStatusError, httpx.RequestError, PydanticValidationError) as exc:
        # HTTPStatusError: Google's token/userinfo endpoint rejected the
        # request (e.g. an already-used or expired code). RequestError:
        # Google could not be reached at all. PydanticValidationError:
        # Google answered, but not with the shape GoogleTokenResponse/
        # GoogleUserInfo expect. All three are the same thing from the
        # caller's side -- the identity provider failed, not something
        # the caller did wrong -- so all three become one clean,
        # typed 502, never a raw unhandled 500.
        raise UpstreamAuthError(
            "Google sign-in could not be completed. Please try again."
        ) from exc

    existing = await find_auth_identity(
        session, provider=AuthProvider.GOOGLE, provider_subject=google_user.sub
    )
    if existing is not None:
        existing.last_login_at = _utc_now()
        session.add(existing)
        await session.commit()
        return existing.user_id

    # First login for this Google identity: User, AuthIdentity, and
    # LearningIdentity are created together in one transaction -- the
    # same add-everything-then-one-commit pattern build_comparison_set
    # uses for its own multi-row insert (api/services/researcher.py) --
    # so a real identity is never left partially created.
    user = User()
    session.add(user)
    await session.flush()

    session.add(
        AuthIdentity(
            user_id=user.id,
            provider=AuthProvider.GOOGLE,
            provider_subject=google_user.sub,
            verified_email=google_user.email,
        )
    )
    session.add(LearningIdentity(user_id=user.id))
    await session.commit()

    return user.id

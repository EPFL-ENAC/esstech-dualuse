from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from api.config import config
from api.db import get_db_session
from api.services.auth import (
    AUTH_SESSION_COOKIE,
    OAUTH_STATE_COOKIE,
    SESSION_COOKIE_MAX_AGE,
    STATE_COOKIE_MAX_AGE,
    build_google_authorize_url,
    cookies_are_secure,
    handle_google_callback,
    sign_session,
    sign_state,
)

router = APIRouter()


@router.get(
    "/auth/google/login",
    summary="Start Google sign-in",
    description=(
        "Redirect to Google's OAuth consent screen (scopes: openid, "
        "email, profile). Sets a short-lived, signed CSRF state cookie, "
        "verified on /auth/google/callback before any token exchange "
        "happens."
    ),
    tags=["Auth"],
)
async def get_google_login() -> RedirectResponse:
    authorize = build_google_authorize_url()
    redirect = RedirectResponse(authorize.url, status_code=302)
    redirect.set_cookie(
        OAUTH_STATE_COOKIE,
        sign_state(authorize.state),
        max_age=STATE_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=cookies_are_secure(),
    )
    return redirect


@router.get(
    "/auth/google/callback",
    summary="Complete Google sign-in",
    description=(
        "Verify the CSRF state, exchange the code for Google's verified "
        "identity, and look up or create the User/AuthIdentity/"
        "LearningIdentity by provider_subject -- never by email. Sets "
        "the real session cookie and redirects to the frontend."
    ),
    tags=["Auth"],
)
async def get_google_callback(
    code: str,
    state: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    state_cookie = request.cookies.get(OAUTH_STATE_COOKIE)
    user_id = await handle_google_callback(
        session, code=code, state=state, state_cookie=state_cookie
    )

    redirect = RedirectResponse(config.APP_URL, status_code=302)
    redirect.delete_cookie(OAUTH_STATE_COOKIE)
    redirect.set_cookie(
        AUTH_SESSION_COOKIE,
        sign_session(user_id),
        max_age=SESSION_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=cookies_are_secure(),
    )
    return redirect


@router.post(
    "/auth/logout",
    summary="Sign out",
    description=(
        "Clear the real session cookie. Never touches the dev cookie "
        "(dev_learner_id) -- that fallback is untouched by this endpoint."
    ),
    tags=["Auth"],
)
async def post_logout(response: Response) -> dict[str, str]:
    response.delete_cookie(AUTH_SESSION_COOKIE)
    return {"detail": "Logged out"}

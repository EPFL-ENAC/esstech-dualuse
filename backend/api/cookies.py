from fastapi import Response

from api.config import config

AUTH_SESSION_COOKIE = "auth_session"
OAUTH_STATE_COOKIE = "oauth_state"
LEARNER_ID_COOKIE = "dev_learner_id"


def set_private_cookie(
    response: Response,
    name: str,
    value: str,
    *,
    max_age: int,
) -> None:
    """Set an HttpOnly, SameSite=Lax cookie, Secure whenever the app is served
    over https (config.APP_URL, the same signal CORS keys off)."""

    response.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=config.APP_URL.startswith("https://"),
    )

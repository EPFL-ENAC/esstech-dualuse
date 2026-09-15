"""Endpoint tests for the Google OAuth login/callback/logout flow.

Most of these share app_client's isolated db_session, the same
convention as every other flow test in this suite. The two
get_current_learner tests near the bottom deliberately call it directly
instead: app_client's fixture overrides get_current_learner outright
(tests/conftest.py), so no test built on app_client ever exercises this
function's real body -- only a direct call does.
"""

from urllib.parse import parse_qs, urlparse
from uuid import UUID

import httpx
from sqlmodel import select
from starlette.requests import Request
from starlette.responses import Response

import api.services.auth as auth_service
from api.config import config
from api.dependencies import LEARNER_ID_COOKIE, get_current_learner
from api.models import AuthIdentity, LearningIdentity, User
from api.services.auth import AUTH_SESSION_COOKIE, GoogleUserInfo, sign_session


def _fake_exchange(sub: str = "google-subject-1", email: str = "learner@example.com"):
    async def _exchange(code: str) -> GoogleUserInfo:
        return GoogleUserInfo(sub=sub, email=email, email_verified=True)

    return _exchange


async def _complete_login(app_client, monkeypatch, *, sub: str, email: str) -> None:
    monkeypatch.setattr(
        auth_service, "exchange_google_code", _fake_exchange(sub, email)
    )

    login = await app_client.get("/auth/google/login", follow_redirects=False)
    state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]

    response = await app_client.get(
        "/auth/google/callback",
        params={"code": "fake-code", "state": state},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == config.APP_URL
    assert AUTH_SESSION_COOKIE in response.cookies


async def test_google_login_redirects_with_scopes_and_state(app_client):
    response = await app_client.get("/auth/google/login", follow_redirects=False)

    assert response.status_code == 302
    location = urlparse(response.headers["location"])
    assert location.netloc == "accounts.google.com"
    query = parse_qs(location.query)
    assert query["scope"] == ["openid email profile"]
    assert query["response_type"] == ["code"]
    assert len(query["state"][0]) > 20
    assert "oauth_state" in response.cookies


async def test_callback_creates_user_identity_and_learning_identity_on_first_login(
    app_client, db_session, monkeypatch
):
    await _complete_login(
        app_client, monkeypatch, sub="google-subject-1", email="learner@example.com"
    )

    users = (await db_session.exec(select(User))).all()
    identities = (await db_session.exec(select(AuthIdentity))).all()
    learning_identities = (await db_session.exec(select(LearningIdentity))).all()

    assert len(users) == 1
    assert len(identities) == 1
    assert identities[0].user_id == users[0].id
    assert identities[0].provider_subject == "google-subject-1"
    assert identities[0].verified_email == "learner@example.com"
    assert len(learning_identities) == 1
    assert learning_identities[0].user_id == users[0].id


async def test_callback_reuses_existing_identity_on_second_login(
    app_client, db_session, monkeypatch
):
    await _complete_login(
        app_client, monkeypatch, sub="google-subject-1", email="learner@example.com"
    )
    (identity_after_first,) = (await db_session.exec(select(AuthIdentity))).all()
    first_login_at = identity_after_first.last_login_at

    await _complete_login(
        app_client, monkeypatch, sub="google-subject-1", email="learner@example.com"
    )

    users = (await db_session.exec(select(User))).all()
    identities = (await db_session.exec(select(AuthIdentity))).all()
    learning_identities = (await db_session.exec(select(LearningIdentity))).all()

    assert len(users) == 1
    assert len(identities) == 1
    assert len(learning_identities) == 1
    assert identities[0].id == identity_after_first.id
    # .replace(tzinfo=None) on both sides: SQLite has no native
    # timezone-aware datetime type, so a value freshly set in Python
    # (aware) and one just read back from a query (naive) are not
    # directly comparable here -- a SQLite-only quirk, not a real
    # discrepancy (Postgres round-trips timezone-aware datetimes fine).
    assert identities[0].last_login_at.replace(tzinfo=None) >= first_login_at.replace(
        tzinfo=None
    )


async def test_callback_missing_state_cookie_is_rejected(app_client, monkeypatch):
    def _fail_if_called(code: str):
        raise AssertionError("exchange_google_code must not run without valid state")

    monkeypatch.setattr(auth_service, "exchange_google_code", _fail_if_called)

    response = await app_client.get(
        "/auth/google/callback",
        params={"code": "fake-code", "state": "whatever-google-sent-back"},
        follow_redirects=False,
    )

    assert response.status_code == 422  # ValidationError: invalid request content
    assert AUTH_SESSION_COOKIE not in response.cookies


async def test_callback_mismatched_state_is_rejected(app_client, monkeypatch):
    def _fail_if_called(code: str):
        raise AssertionError("exchange_google_code must not run without valid state")

    monkeypatch.setattr(auth_service, "exchange_google_code", _fail_if_called)

    login = await app_client.get("/auth/google/login", follow_redirects=False)
    assert "oauth_state" in login.cookies

    response = await app_client.get(
        "/auth/google/callback",
        params={"code": "fake-code", "state": "not-the-state-that-was-issued"},
        follow_redirects=False,
    )

    assert response.status_code == 422  # ValidationError: invalid request content
    assert AUTH_SESSION_COOKIE not in response.cookies


async def test_callback_upstream_google_failure_returns_a_clean_typed_error(
    app_client, monkeypatch
):
    """A failure while talking to Google (network error, Google rejecting
    the code, or a malformed response) must render as a clean, typed 4xx/5xx
    JSON body, the same as every other failure in this project -- never an
    unhandled 500."""

    def _raise_request_error(code: str):
        raise httpx.RequestError("simulated network failure reaching Google")

    monkeypatch.setattr(auth_service, "exchange_google_code", _raise_request_error)

    login = await app_client.get("/auth/google/login", follow_redirects=False)
    state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]

    response = await app_client.get(
        "/auth/google/callback",
        params={"code": "fake-code", "state": state},
        follow_redirects=False,
    )

    assert response.status_code == 502  # UpstreamAuthError: Google's side failed
    body = response.json()
    assert "detail" in body
    assert AUTH_SESSION_COOKIE not in response.cookies


async def test_logout_clears_only_the_real_session_cookie(app_client, monkeypatch):
    await _complete_login(
        app_client, monkeypatch, sub="google-subject-1", email="learner@example.com"
    )
    assert AUTH_SESSION_COOKIE in app_client.cookies

    response = await app_client.post("/auth/logout")

    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "")
    assert AUTH_SESSION_COOKIE in set_cookie
    assert LEARNER_ID_COOKIE not in set_cookie


def _make_request(cookie_header: str = "") -> Request:
    headers = [(b"cookie", cookie_header.encode())] if cookie_header else []
    return Request({"type": "http", "headers": headers, "method": "GET", "path": "/"})


async def test_get_current_learner_resolves_real_session_cookie_via_learning_identity(
    db_session,
):
    user = User()
    db_session.add(user)
    await db_session.flush()
    learning_identity = LearningIdentity(user_id=user.id)
    db_session.add(learning_identity)
    await db_session.commit()

    request = _make_request(f"{AUTH_SESSION_COOKIE}={sign_session(user.id)}")
    response = Response()

    learner_id = await get_current_learner(request, response, session=db_session)

    assert learner_id == learning_identity.learner_id


async def test_get_current_learner_dev_cookie_fallback_is_unchanged(db_session):
    """Regression guard: with no real session cookie, the exact pre-auth
    dev-cookie behavior still runs -- unlike every other test in this
    suite (which goes through app_client's override), this one calls the
    real function directly, so it is the test that actually protects
    tier (b)."""

    request = _make_request()
    response = Response()

    learner_id = await get_current_learner(request, response, session=db_session)

    assert isinstance(learner_id, UUID)
    set_cookie = response.headers.get("set-cookie", "")
    assert LEARNER_ID_COOKIE in set_cookie
    assert str(learner_id) in set_cookie

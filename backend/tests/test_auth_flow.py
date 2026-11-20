"""Endpoint tests for the Google OAuth login/callback/logout flow and the
learner identity resolved from cookies.

exchange_google_code is the only part of this flow that talks to Google, so
it is the one function replaced here.
"""

from urllib.parse import parse_qs, urlparse
from uuid import UUID

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import select

import api.services.auth as auth_service
from api.config import config
from api.cookies import AUTH_SESSION_COOKIE, LEARNER_ID_COOKIE
from api.models import AuthIdentity, LearningIdentity, Session, User
from api.services.auth import GoogleUserInfo, sign_session


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

    assert response.status_code == 422
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

    assert response.status_code == 422
    assert AUTH_SESSION_COOKIE not in response.cookies


async def test_callback_upstream_google_failure_returns_a_clean_typed_error(
    app_client, monkeypatch
):
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

    assert response.status_code == 502
    body = response.json()
    assert "detail" in body
    assert AUTH_SESSION_COOKIE not in response.cookies


async def test_google_login_returns_503_when_not_configured(app_client, monkeypatch):
    monkeypatch.setattr(config, "GOOGLE_CLIENT_ID", None)
    monkeypatch.setattr(config, "GOOGLE_CLIENT_SECRET", None)

    response = await app_client.get("/auth/google/login", follow_redirects=False)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Google sign-in is not configured in this environment"
    }
    assert "oauth_state" not in response.cookies


async def test_google_callback_returns_503_when_not_configured(app_client, monkeypatch):
    def _fail_if_called(code: str):
        raise AssertionError("exchange_google_code must not run when not configured")

    monkeypatch.setattr(auth_service, "exchange_google_code", _fail_if_called)
    monkeypatch.setattr(config, "GOOGLE_CLIENT_ID", None)
    monkeypatch.setattr(config, "GOOGLE_CLIENT_SECRET", None)

    response = await app_client.get(
        "/auth/google/callback",
        params={"code": "fake-code", "state": "whatever-google-sent-back"},
        follow_redirects=False,
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Google sign-in is not configured in this environment"
    }
    assert AUTH_SESSION_COOKIE not in response.cookies


async def test_google_login_returns_503_when_credentials_are_empty_strings(
    app_client, monkeypatch
):
    """frontend/playwright.config.ts forces OAuth dormant for e2e by setting
    both to the empty string, and an empty env var parses to "", never None."""

    monkeypatch.setattr(config, "GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr(config, "GOOGLE_CLIENT_SECRET", "")

    response = await app_client.get("/auth/google/login", follow_redirects=False)

    assert response.status_code == 503


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


@pytest.fixture
async def anonymous_client(db_session):
    """Like app_client, but resolves the learner from cookies for real."""

    from api.db import get_db_session
    from api.main import app

    async def _override_session():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db_session, None)


async def test_signed_session_cookie_acts_as_the_linked_learner(
    anonymous_client, db_session
):
    user = User()
    db_session.add(user)
    await db_session.flush()
    learning_identity = LearningIdentity(user_id=user.id)
    db_session.add(learning_identity)
    await db_session.commit()
    learner_id = learning_identity.learner_id

    anonymous_client.cookies.set(AUTH_SESSION_COOKIE, sign_session(user.id))
    response = await anonymous_client.post("/sessions")

    assert response.status_code == 201
    assert LEARNER_ID_COOKIE not in response.cookies
    created = await db_session.get(Session, UUID(response.json()["id"]))
    assert created is not None
    assert created.learner_id == learner_id


async def test_dev_learner_cookie_is_minted_private_and_reused(anonymous_client):
    response = await anonymous_client.post("/sessions")

    assert response.status_code == 201
    set_cookie = response.headers["set-cookie"].lower()
    assert set_cookie.startswith(f"{LEARNER_ID_COOKIE}=")
    assert "max-age=2592000" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie

    session_id = response.json()["id"]
    learner_cookie = response.cookies[LEARNER_ID_COOKIE]

    anonymous_client.cookies.clear()
    stranger = await anonymous_client.get(f"/sessions/{session_id}/report")
    assert stranger.status_code == 404

    anonymous_client.cookies.clear()
    anonymous_client.cookies.set(LEARNER_ID_COOKIE, learner_cookie)
    owner = await anonymous_client.get(f"/sessions/{session_id}/report")
    assert owner.status_code == 200

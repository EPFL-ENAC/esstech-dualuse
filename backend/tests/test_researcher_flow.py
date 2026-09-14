"""Route-boundary tests for the Researcher route.

The API and these tests share one database session (see the `app_client`
fixture), so fixture rows must be committed before any API call.
"""

import pytest


async def _start_session(app_client, *, route: str | None = None) -> str:
    if route is None:
        response = await app_client.post("/sessions")
    else:
        response = await app_client.post("/sessions", json={"route": route})
    assert response.status_code == 201
    return response.json()["id"]


RESEARCHER_ENDPOINTS = [
    (
        "post",
        "/sessions/{id}/researcher/intake",
        {"raw_description": "a quantum thing"},
    ),
    ("get", "/sessions/{id}/researcher/intake", None),
    ("post", "/sessions/{id}/researcher/tag", {}),
    (
        "post",
        "/sessions/{id}/researcher/gate-and-posture",
        {"gate": "G2", "posture_response": "a competitor"},
    ),
    ("post", "/sessions/{id}/researcher/comparison-set", None),
    (
        "post",
        "/sessions/{id}/researcher/prediction",
        {"predictions": [{"rank": 1, "pattern": "A"}, {"rank": 2, "pattern": "B"}]},
    ),
    ("post", "/sessions/{id}/researcher/reveal", None),
    ("post", "/sessions/{id}/researcher/contrast", {}),
]


@pytest.mark.parametrize("method,path_template,body", RESEARCHER_ENDPOINTS)
async def test_researcher_endpoint_rejects_student_route_session(
    app_client, method, path_template, body
):
    session_id = await _start_session(app_client)  # defaults to Student route
    url = path_template.format(id=session_id)

    if method == "get":
        response = await app_client.get(url)
    elif body is None:
        response = await app_client.post(url)
    else:
        response = await app_client.post(url, json=body)

    assert response.status_code == 409
    assert response.json()["detail"] == "Session is not a Researcher-route session"


async def test_post_sessions_defaults_to_student_route_with_no_body(app_client):
    response = await app_client.post("/sessions")

    assert response.status_code == 201
    assert response.json()["route"] == "student"


async def test_post_sessions_accepts_explicit_researcher_route(app_client):
    session_id = await _start_session(app_client, route="researcher")

    response = await app_client.post(
        f"/sessions/{session_id}/researcher/intake",
        json={"raw_description": "a quantum thing"},
    )

    assert response.status_code == 201
    assert response.json()["mapping_status"] == "unmapped"


async def test_get_intake_404s_before_any_intake_is_started(app_client):
    session_id = await _start_session(app_client, route="researcher")

    response = await app_client.get(f"/sessions/{session_id}/researcher/intake")

    assert response.status_code == 404
    assert response.json()["detail"] == "Technology intake not found"


async def test_get_intake_returns_the_full_stored_state(app_client):
    session_id = await _start_session(app_client, route="researcher")
    await app_client.post(
        f"/sessions/{session_id}/researcher/intake",
        json={"raw_description": "a quantum thing"},
    )
    tag_response = await app_client.post(
        f"/sessions/{session_id}/researcher/tag",
        json={"domain": None, "functions": [], "forms": []},
    )
    assert tag_response.status_code == 200
    assert tag_response.json()["attempts_remaining"] == 1

    response = await app_client.get(f"/sessions/{session_id}/researcher/intake")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["raw_description"] == "a quantum thing"
    assert body["mapping_status"] == "unmapped"
    assert body["attempts_remaining"] == 1
    assert body["gate"] is None
    assert body["posture_response"] is None


async def test_get_intake_before_any_tag_attempt_reports_full_budget(app_client):
    """A fresh, never-tagged intake reports attempts_remaining=2 (the full
    MAX_TAG_ATTEMPTS budget) -- distinct from the 1 a real /tag response
    reports after a single spent attempt, and from the 0 either an
    exhausted or a mapped intake reports."""

    session_id = await _start_session(app_client, route="researcher")
    await app_client.post(
        f"/sessions/{session_id}/researcher/intake",
        json={"raw_description": "a quantum thing"},
    )

    response = await app_client.get(f"/sessions/{session_id}/researcher/intake")

    assert response.status_code == 200
    assert response.json()["attempts_remaining"] == 2

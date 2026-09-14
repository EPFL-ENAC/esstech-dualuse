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
    ("/sessions/{id}/researcher/intake", {"raw_description": "a quantum thing"}),
    ("/sessions/{id}/researcher/tag", {}),
    (
        "/sessions/{id}/researcher/gate-and-posture",
        {"gate": "G2", "posture_response": "a competitor"},
    ),
    ("/sessions/{id}/researcher/comparison-set", None),
    (
        "/sessions/{id}/researcher/prediction",
        {"predictions": [{"rank": 1, "pattern": "A"}, {"rank": 2, "pattern": "B"}]},
    ),
    ("/sessions/{id}/researcher/reveal", None),
    ("/sessions/{id}/researcher/contrast", {}),
]


@pytest.mark.parametrize("path_template,body", RESEARCHER_ENDPOINTS)
async def test_researcher_endpoint_rejects_student_route_session(
    app_client, path_template, body
):
    session_id = await _start_session(app_client)  # defaults to Student route
    url = path_template.format(id=session_id)

    if body is None:
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

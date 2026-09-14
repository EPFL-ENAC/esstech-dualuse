"""Route-boundary tests for the Researcher route.

The API and these tests share one database session (see the `app_client`
fixture), so fixture rows must be committed before any API call.
"""

from uuid import UUID

import pytest

from api.models import Case, ComparisonSet, ComparisonSetCase, CounterCaseLink
from api.models.enums import CaseStatus, CaseType, Domain, Gate, Pattern


async def _start_session(app_client, *, route: str | None = None) -> str:
    if route is None:
        response = await app_client.post("/sessions")
    else:
        response = await app_client.post("/sessions", json={"route": route})
    assert response.status_code == 201
    return response.json()["id"]


def _make_case(title: str, *, case_type: CaseType = CaseType.HARM) -> Case:
    return Case(
        title=title,
        area="counter-case fixture",
        domain=Domain.CYBER_TECHNOLOGIES,
        case_type=case_type,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads="x",
        full_narrative="x",
        main_path_pattern=Pattern.A,
        main_path_gate=Gate.G1,
        source_references=[],
    )


async def _make_comparison_set(
    db_session, *, session_id: str, case_ids: list[UUID]
) -> None:
    """Insert a ComparisonSet + its cases directly.

    Bypasses the real intake/tag/build-comparison-set flow: this file only
    needs a comparison set to exist to test the counter-case lookup, the
    same reasoning test_student_route_guard.py gives for inserting a
    CaseEncounter directly rather than going through create_encounter.
    """

    comparison_set = ComparisonSet(
        session_id=UUID(session_id),
        functions=[],
        was_widened=False,
        case_count=len(case_ids),
    )
    db_session.add(comparison_set)
    await db_session.flush()

    for sequence_no, case_id in enumerate(case_ids):
        db_session.add(
            ComparisonSetCase(
                comparison_set_id=comparison_set.id,
                case_id=case_id,
                inclusion_reason="shared function",
                sequence_no=sequence_no,
            )
        )
    await db_session.commit()


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
    ("get", "/sessions/{id}/researcher/counter-case", None),
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


async def test_get_counter_case_409s_without_a_comparison_set(app_client):
    session_id = await _start_session(app_client, route="researcher")

    response = await app_client.get(f"/sessions/{session_id}/researcher/counter-case")

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Session has no comparison set to check for a counter-case"
    )


async def test_get_counter_case_reports_no_counter_case_for_an_open_area_set(
    app_client, db_session
):
    session_id = await _start_session(app_client, route="researcher")
    harm_case = _make_case("Demo: open-area harm case")
    db_session.add(harm_case)
    await db_session.flush()
    await db_session.commit()
    await _make_comparison_set(
        db_session, session_id=session_id, case_ids=[harm_case.id]
    )

    response = await app_client.get(f"/sessions/{session_id}/researcher/counter-case")

    assert response.status_code == 200
    assert response.json() == {"has_counter_case": False, "counter_case": None}


async def test_get_counter_case_reports_the_linked_counter_case(app_client, db_session):
    session_id = await _start_session(app_client, route="researcher")
    harm_case = _make_case("Demo: twin harm case")
    counter_case = _make_case(
        "Demo: twin counter-case", case_type=CaseType.COUNTER_CASE
    )
    db_session.add(harm_case)
    db_session.add(counter_case)
    await db_session.flush()
    db_session.add(
        CounterCaseLink(
            harm_case_id=harm_case.id,
            counter_case_id=counter_case.id,
            responsibility_posture_contrast="The counter-case redistributes responsibility upstream.",
            gate_lever=Gate.G4,
        )
    )
    await db_session.commit()
    await _make_comparison_set(
        db_session, session_id=session_id, case_ids=[harm_case.id]
    )

    response = await app_client.get(f"/sessions/{session_id}/researcher/counter-case")

    assert response.status_code == 200
    body = response.json()
    assert body["has_counter_case"] is True
    assert body["counter_case"]["counter_case_id"] == str(counter_case.id)
    assert body["counter_case"]["gate_lever"] == "G4"
    assert (
        body["counter_case"]["responsibility_posture_contrast"]
        == "The counter-case redistributes responsibility upstream."
    )

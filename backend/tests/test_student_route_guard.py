"""Every Student-route endpoint rejects a Researcher-route session.

The API and these tests share one database session (see the `app_client`
fixture), so fixture rows must be committed before any API call.
"""

from uuid import UUID

import pytest

from api.models import Case, CaseEncounter
from api.models.enums import CaseStatus, CaseType, Domain, Gate, Pattern

STUDENT_ROUTE_MISMATCH_DETAIL = "Session is not a Student-route session"


def _make_case() -> Case:
    return Case(
        title="Route guard fixture case",
        area="route-guard-tests",
        domain=Domain.CYBER_TECHNOLOGIES,
        case_type=CaseType.HARM,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads="x",
        full_narrative="x",
        main_path_pattern=Pattern.A,
        main_path_gate=Gate.G1,
        source_references=[],
    )


async def _start_researcher_session(app_client) -> str:
    response = await app_client.post("/sessions", json={"route": "researcher"})
    assert response.status_code == 201
    return response.json()["id"]


async def _make_researcher_encounter(db_session, *, session_id: str) -> str:
    """Insert a CaseEncounter on a Researcher-route session.

    The API refuses to create one, so only a direct insert reaches this state.
    """

    case = _make_case()
    db_session.add(case)
    await db_session.flush()

    encounter = CaseEncounter(
        session_id=UUID(session_id), case_id=case.id, sequence_no=1
    )
    db_session.add(encounter)
    await db_session.commit()
    return str(encounter.id)


SESSION_SCOPED_ENDPOINTS = [
    ("post", "/sessions/{id}/intake/diagnostic", {"answers": ["x", "x", "x"]}),
    ("post", "/sessions/{id}/intake/comprehension", {"answer": "x"}),
    ("get", "/sessions/{id}/intake", None),
    (
        "post",
        "/sessions/{id}/encounters",
        {"case_id": "00000000-0000-0000-0000-000000000000"},
    ),
    ("get", "/sessions/{id}/report", None),
]


@pytest.mark.parametrize("method,path_template,body", SESSION_SCOPED_ENDPOINTS)
async def test_session_scoped_student_endpoint_rejects_researcher_route(
    app_client, method, path_template, body
):
    session_id = await _start_researcher_session(app_client)
    url = path_template.format(id=session_id)

    if method == "get":
        response = await app_client.get(url)
    else:
        response = await app_client.post(url, json=body)

    assert response.status_code == 409
    assert response.json()["detail"] == STUDENT_ROUTE_MISMATCH_DETAIL


ENCOUNTER_SCOPED_ENDPOINTS = [
    (
        "post",
        "/encounters/{id}/commitments",
        {"pattern": "A", "gate": "G1", "framing_answers": {}},
    ),
    ("post", "/encounters/{id}/reveal", None),
    ("get", "/encounters/{id}/counter-case", None),
    ("post", "/encounters/{id}/contrast", {}),
]


@pytest.mark.parametrize("method,path_template,body", ENCOUNTER_SCOPED_ENDPOINTS)
async def test_encounter_scoped_student_endpoint_rejects_researcher_route(
    app_client, db_session, method, path_template, body
):
    session_id = await _start_researcher_session(app_client)
    encounter_id = await _make_researcher_encounter(db_session, session_id=session_id)
    url = path_template.format(id=encounter_id)

    if method == "get":
        response = await app_client.get(url)
    else:
        response = await app_client.post(url, json=body)

    assert response.status_code == 409
    assert response.json()["detail"] == STUDENT_ROUTE_MISMATCH_DETAIL

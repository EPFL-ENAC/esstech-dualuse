"""Endpoint tests for the Researcher-route case detail drill-down.

The API and these tests share one database session (see the `app_client`
fixture), so fixture rows must be committed before any API call.
"""

from uuid import UUID, uuid4

from api.models import (
    Case,
    CaseTaggedFunction,
    ComparisonSet,
    ComparisonSetCase,
)
from api.models.enums import (
    CaseStatus,
    CaseType,
    Domain,
    Form,
    Function,
    Gate,
    InclusionReason,
    Pattern,
)


async def _start_session(app_client) -> str:
    response = await app_client.post("/sessions", json={"route": "researcher"})
    assert response.status_code == 201
    return response.json()["id"]


async def _map_intake(app_client, session_id: str) -> None:
    response = await app_client.post(
        f"/sessions/{session_id}/researcher/intake",
        json={"raw_description": "A network traffic anomaly detector."},
    )
    assert response.status_code == 201
    response = await app_client.post(
        f"/sessions/{session_id}/researcher/tag",
        json={
            "domain": Domain.CYBER_TECHNOLOGIES.value,
            "functions": [Function.COMPUTING.value],
            "forms": [Form.PLATFORM.value],
        },
    )
    assert response.status_code == 200
    assert response.json()["mapping_status"] == "mapped"


def _make_case(title: str) -> Case:
    return Case(
        title=title,
        area="case detail fixture",
        domain=Domain.CYBER_TECHNOLOGIES,
        forms=[Form.PLATFORM],
        case_type=CaseType.HARM,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads="Narrative before the crossroads.",
        full_narrative="Full narrative.",
        main_path_pattern=Pattern.A,
        main_path_gate=Gate.G1,
        source_references=["ref-1"],
    )


async def _build_comparison_set(
    db_session,
    *,
    session_id: str,
    cases: list[Case],
    widened_case_ids: frozenset[UUID] = frozenset(),
) -> None:
    """Insert a ComparisonSet, its cases, and one tagged function per case.

    Bypasses the real intake-matching flow, the same reasoning
    test_researcher_report.py's own _build_comparison_set gives: this
    file needs full control over which case belongs to which session's
    set, not a real corpus match.
    """

    for case in cases:
        db_session.add(case)
        db_session.add(CaseTaggedFunction(case_id=case.id, function=Function.COMPUTING))
    await db_session.flush()

    comparison_set = ComparisonSet(
        session_id=UUID(session_id),
        functions=[Function.COMPUTING],
        was_widened=bool(widened_case_ids),
        case_count=len(cases),
    )
    db_session.add(comparison_set)
    await db_session.flush()

    for sequence_no, case in enumerate(cases):
        reason = (
            InclusionReason.WIDENED_BY_DOMAIN
            if case.id in widened_case_ids
            else InclusionReason.SHARED_FUNCTION
        )
        db_session.add(
            ComparisonSetCase(
                comparison_set_id=comparison_set.id,
                case_id=case.id,
                inclusion_reason=reason,
                sequence_no=sequence_no,
            )
        )
    await db_session.commit()


async def _submit_prediction(app_client, session_id: str) -> None:
    response = await app_client.post(
        f"/sessions/{session_id}/researcher/prediction",
        json={
            "predictions": [{"rank": 1, "pattern": "A"}, {"rank": 2, "pattern": "B"}]
        },
    )
    assert response.status_code == 201


async def _get_case_detail(app_client, session_id: str, case_id: UUID) -> dict:
    response = await app_client.get(
        f"/sessions/{session_id}/researcher/cases/{case_id}"
    )
    assert response.status_code == 200
    return response.json()


async def test_case_detail_409s_without_a_comparison_set(app_client):
    session_id = await _start_session(app_client)

    response = await app_client.get(
        f"/sessions/{session_id}/researcher/cases/{uuid4()}"
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Session has no comparison set to look up this case in"
    )


async def test_case_detail_404s_for_a_case_not_in_the_comparison_set(
    app_client, db_session
):
    session_id = await _start_session(app_client)
    await _map_intake(app_client, session_id)
    in_set = _make_case("Case detail fixture: in set")
    not_in_set = _make_case("Case detail fixture: not in set")
    db_session.add(not_in_set)
    await db_session.flush()
    await _build_comparison_set(db_session, session_id=session_id, cases=[in_set])

    response = await app_client.get(
        f"/sessions/{session_id}/researcher/cases/{not_in_set.id}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"


async def test_pre_prediction_case_detail_hides_the_answer_key(app_client, db_session):
    spoilers = (
        "main_path_pattern",
        "main_path_gate",
        "full_narrative",
        "source_references",
    )
    session_id = await _start_session(app_client)
    await _map_intake(app_client, session_id)
    case = _make_case("Case detail fixture: pre-prediction")
    await _build_comparison_set(db_session, session_id=session_id, cases=[case])

    body = await _get_case_detail(app_client, session_id, case.id)

    for field in spoilers:
        assert field not in body


async def test_case_detail_includes_all_fields_once_a_prediction_exists(
    app_client, db_session
):
    session_id = await _start_session(app_client)
    await _map_intake(app_client, session_id)
    case = _make_case("Case detail fixture: post-prediction")
    await _build_comparison_set(
        db_session,
        session_id=session_id,
        cases=[case],
        widened_case_ids=frozenset({case.id}),
    )
    await _submit_prediction(app_client, session_id)

    body = await _get_case_detail(app_client, session_id, case.id)

    assert body["case_id"] == str(case.id)
    assert body["title"] == case.title
    assert body["area"] == case.area
    assert body["narrative_until_crossroads"] == case.narrative_until_crossroads
    assert body["domain"] == Domain.CYBER_TECHNOLOGIES.value
    assert body["functions"] == [Function.COMPUTING.value]
    assert body["forms"] == case.forms
    assert body["inclusion_reason"] == "widened_by_domain"
    assert body["full_narrative"] == case.full_narrative
    assert body["main_path_pattern"] == Pattern.A.value
    assert body["main_path_gate"] == Gate.G1.value
    assert body["source_references"] == case.source_references

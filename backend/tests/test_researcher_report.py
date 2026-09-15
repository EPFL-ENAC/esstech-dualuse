"""Endpoint tests for the Researcher-route session debrief and report.

The API and these tests share one database session (see the `app_client`
fixture), so fixture rows must be committed before any API call.
"""

import re
from uuid import UUID, uuid4

import pytest

from api.models import (
    Case,
    CaseTaggedPattern,
    ComparisonSet,
    ComparisonSetCase,
    CounterCaseLink,
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


async def _start_intake(
    app_client, session_id: str, *, raw_description: str = "A thing."
) -> None:
    response = await app_client.post(
        f"/sessions/{session_id}/researcher/intake",
        json={"raw_description": raw_description},
    )
    assert response.status_code == 201


async def _submit_tag(
    app_client,
    session_id: str,
    *,
    domain: str | None,
    functions: list[str],
    forms: list[str],
) -> dict:
    response = await app_client.post(
        f"/sessions/{session_id}/researcher/tag",
        json={"domain": domain, "functions": functions, "forms": forms},
    )
    assert response.status_code == 200
    return response.json()


async def _map_intake(
    app_client,
    session_id: str,
    *,
    domain: Domain = Domain.CYBER_TECHNOLOGIES,
    functions: list[Function] | None = None,
    forms: list[Form] | None = None,
) -> None:
    functions = [Function.COMPUTING] if functions is None else functions
    forms = [Form.PLATFORM] if forms is None else forms
    result = await _submit_tag(
        app_client,
        session_id,
        domain=domain.value,
        functions=[function.value for function in functions],
        forms=[form.value for form in forms],
    )
    assert result["mapping_status"] == "mapped"


async def _submit_gate_and_posture(
    app_client,
    session_id: str,
    *,
    gate: Gate = Gate.G3,
    posture_response: str = "a competitor",
) -> None:
    response = await app_client.post(
        f"/sessions/{session_id}/researcher/gate-and-posture",
        json={"gate": gate.value, "posture_response": posture_response},
    )
    assert response.status_code == 201


def _make_case(title: str, *, case_type: CaseType = CaseType.HARM) -> Case:
    return Case(
        title=title,
        area="report fixture",
        domain=Domain.CYBER_TECHNOLOGIES,
        case_type=case_type,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads="x",
        full_narrative="x",
        main_path_pattern=Pattern.A,
        main_path_gate=Gate.G1,
        source_references=[],
    )


async def _build_comparison_set(
    db_session,
    *,
    session_id: str,
    cases_and_patterns: list[tuple[Case, list[Pattern]]],
    was_widened: bool = False,
) -> None:
    """Insert a ComparisonSet, its cases, and their tagged patterns directly.

    Bypasses the real intake-matching flow, the same reasoning
    test_researcher_flow.py's own _make_comparison_set gives: this file
    needs full control over the resulting pattern distribution, not a
    real corpus match.
    """

    for case, _ in cases_and_patterns:
        db_session.add(case)
    await db_session.flush()

    comparison_set = ComparisonSet(
        session_id=UUID(session_id),
        functions=[],
        was_widened=was_widened,
        case_count=len(cases_and_patterns),
    )
    db_session.add(comparison_set)
    await db_session.flush()

    for sequence_no, (case, patterns) in enumerate(cases_and_patterns):
        db_session.add(
            ComparisonSetCase(
                comparison_set_id=comparison_set.id,
                case_id=case.id,
                inclusion_reason=InclusionReason.SHARED_FUNCTION,
                sequence_no=sequence_no,
            )
        )
        for pattern in patterns:
            db_session.add(CaseTaggedPattern(case_id=case.id, pattern=pattern))
    await db_session.commit()


async def _submit_prediction(
    app_client, session_id: str, predictions: list[dict]
) -> None:
    response = await app_client.post(
        f"/sessions/{session_id}/researcher/prediction",
        json={"predictions": predictions},
    )
    assert response.status_code == 201


async def _submit_contrast(
    app_client, session_id: str, learner_response: str | None
) -> None:
    response = await app_client.post(
        f"/sessions/{session_id}/researcher/contrast",
        json={"learner_response": learner_response},
    )
    assert response.status_code == 200


async def _get_report(app_client, session_id: str) -> dict:
    response = await app_client.get(f"/sessions/{session_id}/researcher/report")
    assert response.status_code == 200
    return response.json()


async def _in_progress_session(app_client, db_session) -> str:
    return await _start_session(app_client)


async def _boundary_exit_session(app_client, db_session) -> str:
    """Two /tag attempts, both still incomplete, exhausting the budget.

    functions is identical across both calls (only forms differs) -- this
    exercises the retry-count exhaustion path, not two attempts with
    genuinely different content. Fine for what this file tests (the
    report's own boundary_exit derivation), but worth strengthening with
    two truly different submissions if submit_tag itself ever needs new
    coverage here.
    """

    session_id = await _start_session(app_client)
    await _start_intake(app_client, session_id)
    await _submit_tag(
        app_client, session_id, domain=None, functions=["sensing"], forms=[]
    )
    await _submit_tag(
        app_client, session_id, domain=None, functions=["sensing"], forms=["device"]
    )
    return session_id


async def _full_session(app_client, db_session) -> str:
    """Mapped, matching prediction, open-area contrast: dominant=A, secondary=[B]."""

    session_id = await _start_session(app_client)
    await _start_intake(app_client, session_id)
    await _map_intake(app_client, session_id)
    await _submit_gate_and_posture(app_client, session_id)
    case1 = _make_case("Report fixture: full 1")
    case2 = _make_case("Report fixture: full 2")
    await _build_comparison_set(
        db_session,
        session_id=session_id,
        cases_and_patterns=[(case1, [Pattern.A]), (case2, [Pattern.B])],
    )
    await _submit_prediction(
        app_client,
        session_id,
        [{"rank": 1, "pattern": "A"}, {"rank": 2, "pattern": "B"}],
    )
    await _submit_contrast(app_client, session_id, None)
    return session_id


async def _zero_pattern_session(app_client, db_session) -> str:
    session_id = await _start_session(app_client)
    await _start_intake(app_client, session_id)
    await _map_intake(app_client, session_id)
    await _submit_gate_and_posture(app_client, session_id)
    case = _make_case("Report fixture: untagged")
    await _build_comparison_set(
        db_session, session_id=session_id, cases_and_patterns=[(case, [])]
    )
    await _submit_prediction(
        app_client,
        session_id,
        [{"rank": 1, "pattern": "A"}, {"rank": 2, "pattern": "B"}],
    )
    await _submit_contrast(app_client, session_id, None)
    return session_id


async def test_report_is_in_progress_before_any_intake(app_client):
    session_id = await _start_session(app_client)

    body = await _get_report(app_client, session_id)

    assert body == {"trace_completeness": "in_progress"}


async def test_report_is_in_progress_mid_mapping_with_attempts_remaining(app_client):
    session_id = await _start_session(app_client)
    await _start_intake(app_client, session_id)
    await _submit_tag(app_client, session_id, domain=None, functions=[], forms=[])

    body = await _get_report(app_client, session_id)

    assert body == {"trace_completeness": "in_progress"}


async def test_report_is_in_progress_once_mapped_but_before_contrast(app_client):
    session_id = await _start_session(app_client)
    await _start_intake(app_client, session_id)
    await _map_intake(app_client, session_id)
    await _submit_gate_and_posture(app_client, session_id)

    body = await _get_report(app_client, session_id)

    assert body == {"trace_completeness": "in_progress"}


async def test_report_is_boundary_exit_once_tag_attempts_are_exhausted(
    app_client, db_session
):
    session_id = await _boundary_exit_session(app_client, db_session)

    body = await _get_report(app_client, session_id)

    assert body["trace_completeness"] == "boundary_exit"
    assert "domain" not in body  # never entered during either attempt
    assert body["functions"] == ["sensing"]
    assert body["forms"] == ["device"]
    assert body["reflection_prompt_key"] == "researcherReflectionBoundaryExit"
    assert "gate" not in body
    assert "case_count" not in body
    assert "predictions" not in body
    assert "contrast_type" not in body


async def test_report_full_with_matching_prediction_and_open_area(
    app_client, db_session
):
    session_id = await _full_session(app_client, db_session)

    body = await _get_report(app_client, session_id)

    assert body["trace_completeness"] == "full"
    assert body["domain"] == "Cyber Technologies"
    assert body["functions"] == ["computing"]
    assert body["forms"] == ["platform"]
    assert body["gate"] == "G3"
    assert body["posture_response"] == "a competitor"
    assert body["case_count"] == 2
    assert body["was_widened"] is False
    assert body["predictions"] == [
        {"rank": 1, "pattern": "A"},
        {"rank": 2, "pattern": "B"},
    ]
    assert body["dominant_pattern"] == "A"
    assert body["secondary_patterns"] == ["B"]
    assert body["top_prediction_is_dominant"] is True
    assert body["contrast_type"] == "open_area"
    assert "learner_response" not in body  # always None for open_area, so omitted
    assert body["reflection_prompt_key"] == "researcherReflectionFullMatchesDominant"
    assert "gate_lever" not in body


async def test_report_full_with_mismatched_prediction_and_twin_counter_case(
    app_client, db_session
):
    session_id = await _start_session(app_client)
    await _start_intake(app_client, session_id)
    await _map_intake(app_client, session_id)
    await _submit_gate_and_posture(app_client, session_id)

    harm_case = _make_case("Report fixture: twin harm")
    db_session.add(harm_case)
    await db_session.flush()
    counter_case = _make_case(
        "Report fixture: twin counter-case", case_type=CaseType.COUNTER_CASE
    )
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
    await _build_comparison_set(
        db_session, session_id=session_id, cases_and_patterns=[(harm_case, [Pattern.B])]
    )
    await _submit_prediction(
        app_client,
        session_id,
        [{"rank": 1, "pattern": "A"}, {"rank": 2, "pattern": "B"}],
    )
    await _submit_contrast(
        app_client, session_id, "The counter-case shifts who is responsible."
    )

    body = await _get_report(app_client, session_id)

    assert body["trace_completeness"] == "full"
    assert body["dominant_pattern"] == "B"
    assert body["top_prediction_is_dominant"] is False
    assert body["contrast_type"] == "twin_counter_case"
    assert body["learner_response"] == "The counter-case shifts who is responsible."
    assert body["gate_lever"] == "G4"
    assert body["reflection_prompt_key"] == "researcherReflectionFullDoesNotMatch"


async def test_report_zero_pattern_when_no_case_carries_a_tagged_pattern(
    app_client, db_session
):
    session_id = await _zero_pattern_session(app_client, db_session)

    body = await _get_report(app_client, session_id)

    assert body["trace_completeness"] == "zero_pattern"
    assert "dominant_pattern" not in body
    assert body["secondary_patterns"] == []
    assert "top_prediction_is_dominant" not in body
    assert body["contrast_type"] == "open_area"
    assert body["reflection_prompt_key"] == "researcherReflectionZeroPattern"


async def test_another_learners_session_report_is_not_found(
    app_client, db_session, learner
):
    session_id = await _start_session(app_client)

    learner["id"] = uuid4()
    response = await app_client.get(f"/sessions/{session_id}/researcher/report")

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


@pytest.mark.parametrize(
    "build_session",
    [
        _in_progress_session,
        _boundary_exit_session,
        _full_session,
        _zero_pattern_session,
    ],
)
async def test_report_never_contains_forbidden_score_or_verdict_language(
    app_client, db_session, build_session
):
    session_id = await build_session(app_client, db_session)

    response = await app_client.get(f"/sessions/{session_id}/researcher/report")

    for pattern in (r"\bscores?\b", r"\bverdicts?\b", r"\bcorrect\b", r"\bincorrect\b"):
        assert not re.search(pattern, response.text, re.IGNORECASE)

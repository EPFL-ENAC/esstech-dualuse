"""Endpoint tests for the M6/M7 session debrief and reflection report.

The API and these tests share one database session (see the `app_client`
fixture), so fixture rows must be committed before any API call.
"""

import re
from uuid import uuid4

import pytest

from api.models import Case, CounterCaseLink
from api.models.enums import CaseStatus, CaseType, Domain, Gate, MatchResult, Pattern


def _make_case(
    title: str = "Case 1",
    *,
    main_path_pattern: Pattern = Pattern.A,
    main_path_gate: Gate = Gate.G1,
    case_type: CaseType = CaseType.HARM,
) -> Case:
    return Case(
        title=title,
        area="area-1",
        domain=Domain.ARTIFICIAL_INTELLIGENCE,
        case_type=case_type,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads="Narrative before the crossroads.",
        full_narrative="Full narrative.",
        main_path_pattern=main_path_pattern,
        main_path_gate=main_path_gate,
        source_references=[],
    )


async def _link_counter_case(
    db_session, *, harm_case: Case, gate_lever: Gate
) -> CounterCaseLink:
    counter_case = Case(
        title=f"{harm_case.title} (counter-case)",
        area=harm_case.area,
        domain=harm_case.domain,
        case_type=CaseType.COUNTER_CASE,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads="Counter-case narrative.",
        full_narrative="Counter-case full narrative.",
        main_path_pattern=Pattern.B,
        main_path_gate=Gate.G2,
        source_references=[],
    )
    db_session.add(counter_case)
    await db_session.flush()

    link = CounterCaseLink(
        harm_case_id=harm_case.id,
        counter_case_id=counter_case.id,
        responsibility_posture_contrast="The counter-case redistributes responsibility upstream.",
        gate_lever=gate_lever,
    )
    db_session.add(link)
    await db_session.commit()
    return link


async def _start_session(app_client) -> str:
    response = await app_client.post("/sessions")
    assert response.status_code == 201
    return response.json()["id"]


async def _select_case(app_client, session_id: str, case: Case) -> str:
    response = await app_client.post(
        f"/sessions/{session_id}/encounters", json={"case_id": str(case.id)}
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _commit_to(
    app_client, encounter_id: str, *, pattern: Pattern, gate: Gate
) -> None:
    response = await app_client.post(
        f"/encounters/{encounter_id}/commitments",
        json={"pattern": pattern.value, "gate": gate.value, "framing_answers": {}},
    )
    assert response.status_code == 201


async def _reveal(app_client, encounter_id: str) -> None:
    response = await app_client.post(f"/encounters/{encounter_id}/reveal")
    assert response.status_code == 200


async def _submit_contrast(
    app_client, encounter_id: str, learner_response: str | None
) -> None:
    response = await app_client.post(
        f"/encounters/{encounter_id}/contrast",
        json={"learner_response": learner_response},
    )
    assert response.status_code == 200


async def _complete_encounter(
    app_client,
    db_session,
    session_id: str,
    case: Case,
    *,
    pattern: Pattern,
    gate: Gate,
    learner_response: str | None = None,
) -> str:
    """Persist `case` and walk one encounter through commit, reveal, contrast."""

    db_session.add(case)
    await db_session.commit()

    encounter_id = await _select_case(app_client, session_id, case)
    await _commit_to(app_client, encounter_id, pattern=pattern, gate=gate)
    await _reveal(app_client, encounter_id)
    await _submit_contrast(app_client, encounter_id, learner_response)
    return encounter_id


async def _get_report(app_client, session_id: str) -> dict:
    response = await app_client.get(f"/sessions/{session_id}/report")
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize(
    ("pattern", "gate", "expected"),
    [
        (Pattern.A, Gate.G1, MatchResult.MATCH),
        (Pattern.A, Gate.G2, MatchResult.PARTIAL_MATCH),
        (Pattern.B, Gate.G2, MatchResult.MISMATCH),
    ],
)
async def test_report_single_open_area_encounter_per_match_result(
    app_client, db_session, pattern, gate, expected
):
    case = _make_case(main_path_pattern=Pattern.A, main_path_gate=Gate.G1)
    session_id = await _start_session(app_client)
    await _complete_encounter(
        app_client, db_session, session_id, case, pattern=pattern, gate=gate
    )

    body = await _get_report(app_client, session_id)

    assert body["has_completed_cases"] is True
    (entry,) = body["report"]["encounters"]
    assert entry["case_title"] == case.title
    assert entry["domain"] == Domain.ARTIFICIAL_INTELLIGENCE.value
    assert entry["committed_pattern"] == pattern.value
    assert entry["committed_gate"] == gate.value
    assert entry["match_result"] == expected.value
    assert entry["contrast_type"] == "open_area"
    assert "gate_lever" not in entry


async def test_report_twin_counter_case_encounter_includes_gate_lever(
    app_client, db_session
):
    case = _make_case()
    db_session.add(case)
    await db_session.commit()
    link = await _link_counter_case(db_session, harm_case=case, gate_lever=Gate.G4)
    session_id = await _start_session(app_client)
    await _complete_encounter(
        app_client,
        db_session,
        session_id,
        case,
        pattern=Pattern.A,
        gate=Gate.G1,
        learner_response="The counter-case shifts who is responsible.",
    )

    body = await _get_report(app_client, session_id)

    (entry,) = body["report"]["encounters"]
    assert entry["contrast_type"] == "twin_counter_case"
    assert entry["gate_lever"] == link.gate_lever.value == Gate.G4.value


async def _build_three_encounter_session(app_client, db_session) -> str:
    """A session with 3 completed encounters: two open-area, one twin.

    Chosen so patterns and gates overlap on purpose: encounter 1 and 2 both
    commit to Pattern.A (dedup should collapse patterns_selected to 2 unique
    values, not 3), while every gate differs (3 unique decision points).
    """

    session_id = await _start_session(app_client)

    case1 = _make_case("Case 1", main_path_pattern=Pattern.A, main_path_gate=Gate.G1)
    await _complete_encounter(
        app_client, db_session, session_id, case1, pattern=Pattern.A, gate=Gate.G1
    )  # MATCH, open_area

    case2 = _make_case("Case 2", main_path_pattern=Pattern.B, main_path_gate=Gate.G2)
    db_session.add(case2)
    await db_session.commit()
    link = await _link_counter_case(db_session, harm_case=case2, gate_lever=Gate.G4)
    await _complete_encounter(
        app_client,
        db_session,
        session_id,
        case2,
        pattern=Pattern.A,
        gate=Gate.G2,
        learner_response="A different team held responsibility.",
    )  # PARTIAL_MATCH, twin_counter_case, gate_lever=G4

    case3 = _make_case("Case 3", main_path_pattern=Pattern.C, main_path_gate=Gate.G3)
    await _complete_encounter(
        app_client, db_session, session_id, case3, pattern=Pattern.C, gate=Gate.G3
    )  # MATCH, open_area

    assert link.gate_lever == Gate.G4
    return session_id


async def test_report_aggregates_across_multiple_encounters(app_client, db_session):
    session_id = await _build_three_encounter_session(app_client, db_session)

    body = await _get_report(app_client, session_id)
    report = body["report"]

    assert report["cases_explored"] == 3
    assert sorted(report["decision_points_considered"]) == ["G1", "G2", "G3"]
    assert sorted(report["patterns_selected"]) == ["A", "C"]
    assert report["match_result_counts"] == {
        "match": 2,
        "partial_match": 1,
        "mismatch": 0,
    }


async def test_counter_case_reflections_completed_equals_cases_explored(
    app_client, db_session
):
    session_id = await _build_three_encounter_session(app_client, db_session)

    body = await _get_report(app_client, session_id)
    report = body["report"]

    assert report["counter_case_reflections_completed"] == report["cases_explored"]


async def test_suggested_next_focus_reflects_the_counter_case_gate_lever(
    app_client, db_session
):
    session_id = await _build_three_encounter_session(app_client, db_session)

    body = await _get_report(app_client, session_id)

    assert body["report"]["suggested_next_focus"] == Gate.G4.value


async def test_suggested_next_focus_omitted_when_no_counter_case_exists(
    app_client, db_session
):
    session_id = await _start_session(app_client)
    case = _make_case()
    await _complete_encounter(
        app_client, db_session, session_id, case, pattern=Pattern.A, gate=Gate.G1
    )

    body = await _get_report(app_client, session_id)

    assert "suggested_next_focus" not in body["report"]


async def test_has_completed_cases_false_before_reveal(app_client, db_session):
    case = _make_case()
    db_session.add(case)
    await db_session.commit()
    session_id = await _start_session(app_client)
    encounter_id = await _select_case(app_client, session_id, case)
    await _commit_to(app_client, encounter_id, pattern=Pattern.A, gate=Gate.G1)

    body = await _get_report(app_client, session_id)

    assert body["has_completed_cases"] is False
    assert "report" not in body


async def test_has_completed_cases_false_after_reveal_before_contrast(
    app_client, db_session
):
    """Commitment and FeedbackRecord exist, but contrast has not been
    submitted yet -- the exact boundary the strict definition excludes.

    Only reachable by hitting this endpoint directly mid-encounter: the
    Another-case/Finish card in StudentEncounterPage.vue is
    v-if="contrast", so no normal navigation leaves an encounter in this
    state before moving on.
    """

    case = _make_case()
    db_session.add(case)
    await db_session.commit()
    session_id = await _start_session(app_client)
    encounter_id = await _select_case(app_client, session_id, case)
    await _commit_to(app_client, encounter_id, pattern=Pattern.A, gate=Gate.G1)
    await _reveal(app_client, encounter_id)

    body = await _get_report(app_client, session_id)

    assert body["has_completed_cases"] is False
    assert "report" not in body


async def test_another_learners_session_is_not_found(app_client, db_session, learner):
    session_id = await _start_session(app_client)

    learner["id"] = uuid4()
    response = await app_client.get(f"/sessions/{session_id}/report")

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


async def test_report_never_contains_forbidden_score_or_grade_language(
    app_client, db_session
):
    session_id = await _build_three_encounter_session(app_client, db_session)

    response = await app_client.get(f"/sessions/{session_id}/report")
    text = response.text

    assert not re.search(r"\bscores?\b", text, re.IGNORECASE)
    assert not re.search(r"\bgrades?\b", text, re.IGNORECASE)

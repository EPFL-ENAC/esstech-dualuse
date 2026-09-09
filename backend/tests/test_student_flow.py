"""Endpoint tests for the Student/Individual slice.

The API and these tests share one database session (see the `app_client`
fixture), so fixture rows must be committed before any API call.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlmodel import select

from api.models import Case, Commitment, FeedbackRecord
from api.models.enums import CaseStatus, CaseType, Gate, MatchResult, Pattern
from api.services.feedback import compute_match_result


def _make_case(
    title: str = "Case 1",
    *,
    main_path_pattern: Pattern = Pattern.A,
    main_path_gate: Gate = Gate.G1,
    status: CaseStatus = CaseStatus.PUBLISHED,
    case_type: CaseType = CaseType.HARM,
) -> Case:
    return Case(
        title=title,
        area="area-1",
        case_type=case_type,
        status=status,
        narrative_until_crossroads="Narrative before the crossroads.",
        full_narrative="Full narrative.",
        main_path_pattern=main_path_pattern,
        main_path_gate=main_path_gate,
        source_references=["ref-1"],
    )


def _instant(value: str) -> datetime:
    """Parse an API timestamp, tolerating SQLite's tz-less round-trip.

    Postgres stores `revealed_at` as timestamptz and returns it tz-aware
    whether the reveal computed the row or re-read it. SQLite drops the offset
    on read, so here the freshly computed and re-fetched values serialize to
    different strings while denoting the same instant. Compare instants, not
    strings, so this test asserts the invariant rather than the test backend.
    """

    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


async def _start_session(app_client) -> str:
    response = await app_client.post("/sessions")
    assert response.status_code == 201
    return response.json()["id"]


async def _select_case(app_client, session_id: str, case: Case):
    return await app_client.post(
        f"/sessions/{session_id}/encounters", json={"case_id": str(case.id)}
    )


async def _commit_to(app_client, encounter_id: str, *, pattern: Pattern, gate: Gate):
    return await app_client.post(
        f"/encounters/{encounter_id}/commitments",
        json={
            "pattern": pattern.value,
            "gate": gate.value,
            "framing_answers": {"q1": "a1"},
        },
    )


async def _encounter_for(app_client, db_session, case: Case) -> str:
    """Persist `case`, start a session, select it, and return the encounter id."""

    db_session.add(case)
    await db_session.commit()

    session_id = await _start_session(app_client)
    response = await _select_case(app_client, session_id, case)
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.parametrize(
    ("pattern", "gate", "expected"),
    [
        (Pattern.A, Gate.G1, MatchResult.MATCH),
        (Pattern.A, Gate.G2, MatchResult.PARTIAL_MATCH),
        (Pattern.B, Gate.G1, MatchResult.PARTIAL_MATCH),
        (Pattern.B, Gate.G2, MatchResult.MISMATCH),
    ],
)
def test_compute_match_result(pattern, gate, expected):
    case = _make_case(main_path_pattern=Pattern.A, main_path_gate=Gate.G1)
    commitment = Commitment(
        case_encounter_id=uuid4(), sequence_no=1, pattern=pattern, gate=gate
    )

    assert compute_match_result(commitment=commitment, case=case) is expected


@pytest.mark.parametrize(
    ("pattern", "gate", "expected"),
    [
        (Pattern.A, Gate.G1, MatchResult.MATCH),
        (Pattern.A, Gate.G2, MatchResult.PARTIAL_MATCH),
        (Pattern.B, Gate.G2, MatchResult.MISMATCH),
    ],
)
async def test_reveal_returns_match_result(
    app_client, db_session, pattern, gate, expected
):
    case = _make_case(main_path_pattern=Pattern.A, main_path_gate=Gate.G1)
    encounter_id = await _encounter_for(app_client, db_session, case)
    committed = await _commit_to(app_client, encounter_id, pattern=pattern, gate=gate)
    assert committed.status_code == 201

    response = await app_client.post(f"/encounters/{encounter_id}/reveal")

    assert response.status_code == 200
    body = response.json()
    assert body["match_result"] == expected.value
    assert body["case"]["full_narrative"] == "Full narrative."
    assert body["case"]["main_path_pattern"] == Pattern.A.value
    assert body["commitment"] == {"pattern": pattern.value, "gate": gate.value}


async def test_reveal_twice_returns_the_identical_record(app_client, db_session):
    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)
    await _commit_to(app_client, encounter_id, pattern=Pattern.A, gate=Gate.G1)

    first = await app_client.post(f"/encounters/{encounter_id}/reveal")
    second = await app_client.post(f"/encounters/{encounter_id}/reveal")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["feedback_record_id"] == second.json()["feedback_record_id"]
    assert _instant(first.json()["revealed_at"]) == _instant(
        second.json()["revealed_at"]
    )

    records = (await db_session.exec(select(FeedbackRecord))).all()
    assert len(records) == 1


async def test_reveal_falls_back_to_the_existing_record_when_the_insert_loses(
    app_client, db_session, monkeypatch
):
    """The race branch, simulated rather than observed.

    This forces the initial lookup to miss so the INSERT hits the real UNIQUE
    constraint. It does NOT reproduce genuine concurrency: the test fixture's
    single SQLite connection serializes writers, so the Postgres behaviour this
    branch relies on -- the losing INSERT blocking until the winner commits,
    making the row visible on re-fetch -- is not verified here.
    """

    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)
    await _commit_to(app_client, encounter_id, pattern=Pattern.A, gate=Gate.G1)

    commitment = (await db_session.exec(select(Commitment))).one()
    winner = FeedbackRecord(
        case_encounter_id=commitment.case_encounter_id,
        commitment_id=commitment.id,
        match_result=MatchResult.MISMATCH,
    )
    db_session.add(winner)
    await db_session.commit()

    from api.services import feedback as feedback_service

    real_find = feedback_service._find_record
    calls = {"count": 0}

    async def _miss_once(session, *, encounter_id):
        calls["count"] += 1
        if calls["count"] == 1:
            return None
        return await real_find(session, encounter_id=encounter_id)

    monkeypatch.setattr(feedback_service, "_find_record", _miss_once)

    response = await app_client.post(f"/encounters/{encounter_id}/reveal")

    assert response.status_code == 200
    body = response.json()
    # The winner's verdict survives, rather than being recomputed or restamped.
    assert body["feedback_record_id"] == str(winner.id)
    assert body["match_result"] == MatchResult.MISMATCH.value

    records = (await db_session.exec(select(FeedbackRecord))).all()
    assert len(records) == 1


async def test_selecting_the_same_case_twice_is_rejected(app_client, db_session):
    case = _make_case()
    db_session.add(case)
    await db_session.commit()
    session_id = await _start_session(app_client)

    assert (await _select_case(app_client, session_id, case)).status_code == 201
    duplicate = await _select_case(app_client, session_id, case)

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Case already selected in this session"


async def test_fourth_encounter_in_a_session_is_rejected(app_client, db_session):
    cases = [_make_case(f"Case {index}") for index in range(1, 5)]
    for case in cases:
        db_session.add(case)
    await db_session.commit()
    session_id = await _start_session(app_client)

    for case in cases[:3]:
        assert (await _select_case(app_client, session_id, case)).status_code == 201

    fourth = await _select_case(app_client, session_id, cases[3])

    assert fourth.status_code == 409
    assert fourth.json()["detail"] == "Session cannot accept another encounter"


async def test_second_commitment_on_the_same_encounter_is_rejected(
    app_client, db_session
):
    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)

    first = await _commit_to(app_client, encounter_id, pattern=Pattern.A, gate=Gate.G1)
    second = await _commit_to(app_client, encounter_id, pattern=Pattern.B, gate=Gate.G2)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == "Encounter already has a commitment"

    commitments = (await db_session.exec(select(Commitment))).all()
    assert len(commitments) == 1


async def test_candidates_exclude_cases_encountered_in_any_earlier_session(
    app_client, db_session
):
    seen, unseen = _make_case("Case 1"), _make_case("Case 2")
    db_session.add(seen)
    db_session.add(unseen)
    await db_session.commit()

    first_session = await _start_session(app_client)
    assert (await _select_case(app_client, first_session, seen)).status_code == 201

    await _start_session(app_client)
    response = await app_client.get("/cases/candidates")

    assert response.status_code == 200
    assert [case["title"] for case in response.json()] == ["Case 2"]


async def test_candidates_exclude_unpublished_and_counter_cases(app_client, db_session):
    published = _make_case("Case 1")
    draft = _make_case("Case 2", status=CaseStatus.DRAFT)
    counter = _make_case("Case 3", case_type=CaseType.COUNTER_CASE)
    for case in (published, draft, counter):
        db_session.add(case)
    await db_session.commit()

    response = await app_client.get("/cases/candidates")

    assert [case["title"] for case in response.json()] == ["Case 1"]


async def test_pre_reveal_responses_hide_the_answer_key(app_client, db_session):
    spoilers = ("full_narrative", "main_path_pattern", "main_path_gate")
    case = _make_case()
    db_session.add(case)
    await db_session.commit()
    session_id = await _start_session(app_client)

    candidates = await app_client.get("/cases/candidates")
    encounter = await _select_case(app_client, session_id, case)

    assert candidates.status_code == 200
    assert encounter.status_code == 201
    for field in spoilers:
        assert field not in candidates.json()[0]
        assert field not in encounter.json()["case"]


async def test_another_learners_session_is_not_found(app_client, db_session, learner):
    case = _make_case()
    db_session.add(case)
    await db_session.commit()
    session_id = await _start_session(app_client)

    learner["id"] = uuid4()
    response = await _select_case(app_client, session_id, case)

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


async def test_another_learners_encounter_is_not_found(app_client, db_session, learner):
    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)

    learner["id"] = uuid4()
    commitment = await _commit_to(
        app_client, encounter_id, pattern=Pattern.A, gate=Gate.G1
    )
    reveal = await app_client.post(f"/encounters/{encounter_id}/reveal")

    assert commitment.status_code == 404
    assert reveal.status_code == 404


async def test_reveal_without_a_commitment_is_rejected(app_client, db_session):
    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)

    response = await app_client.post(f"/encounters/{encounter_id}/reveal")

    assert response.status_code == 409
    assert response.json()["detail"] == "Encounter has no commitment to reveal"

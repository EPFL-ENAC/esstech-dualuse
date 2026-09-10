"""Endpoint tests for the M0 intake slice.

The API and these tests share one database session (see the `app_client`
fixture), so fixture rows must be committed before any API call.

Every assertion about content here is against PLACEHOLDER material in
api/content/intake_key.py. When that file is replaced with real assessment
items, the correct-option ids below change with it -- these tests pin the
*mechanism* (scoring, thresholds, one-shot finalization, key confidentiality),
not the pedagogy.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlmodel import select

from api.content.intake_key import (
    COMPREHENSION_ITEM,
    DIAGNOSTIC_ITEMS,
    DIAGNOSTIC_THRESHOLD,
)
from api.models import SessionIntake
from api.models.enums import ScaffoldingDepth

# Placeholder-content shorthands, derived from the key rather than hardcoded,
# so a change to the key data does not silently invalidate these tests.
ALL_CORRECT = [item.correct for item in DIAGNOSTIC_ITEMS]
ALL_WRONG = [
    next(option for option in item.options if option != item.correct)
    for item in DIAGNOSTIC_ITEMS
]
ONE_CORRECT = [ALL_CORRECT[0], *ALL_WRONG[1:]]
WRONG_COMPREHENSION = next(
    option
    for option in COMPREHENSION_ITEM.options
    if option != COMPREHENSION_ITEM.correct
)


def _instant(value: str) -> datetime:
    """Parse an API timestamp, tolerating SQLite's tz-less round-trip.

    Same reasoning as the reveal tests: SQLite drops the offset on read, so a
    freshly written and a re-fetched value serialize differently while denoting
    the same instant. Compare instants, not strings.
    """

    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


async def _start_session(app_client) -> str:
    response = await app_client.post("/sessions")
    assert response.status_code == 201
    return response.json()["id"]


async def _diagnostic(app_client, session_id: str, answers: list[str]):
    return await app_client.post(
        f"/sessions/{session_id}/intake/diagnostic", json={"answers": answers}
    )


async def _comprehension(app_client, session_id: str, answer: str):
    return await app_client.post(
        f"/sessions/{session_id}/intake/comprehension", json={"answer": answer}
    )


@pytest.mark.parametrize(
    ("answers", "expected_score"),
    [
        (ALL_CORRECT, 3),
        (ONE_CORRECT, 1),
        (ALL_WRONG, 0),
    ],
)
async def test_diagnostic_scores_against_the_key(app_client, answers, expected_score):
    session_id = await _start_session(app_client)

    response = await _diagnostic(app_client, session_id, answers)

    assert response.status_code == 201
    body = response.json()
    assert body["diagnostic_score"] == expected_score
    assert body["above_threshold"] is (expected_score >= DIAGNOSTIC_THRESHOLD)


async def test_primer_is_shown_exactly_when_below_threshold(app_client, db_session):
    """`primer_shown` is derived server-side; no request body carries it."""

    below = await _start_session(app_client)
    await _diagnostic(app_client, below, ALL_WRONG)
    above = await _start_session(app_client)
    await _diagnostic(app_client, above, ALL_CORRECT)

    rows = {
        str(row.session_id): row
        for row in (await db_session.exec(select(SessionIntake))).all()
    }

    assert rows[below].primer_shown is True
    assert rows[above].primer_shown is False


async def test_diagnostic_twice_returns_the_identical_result(app_client, db_session):
    session_id = await _start_session(app_client)

    first = await _diagnostic(app_client, session_id, ALL_CORRECT)
    # A different, worse set of answers must not overwrite the stored score.
    second = await _diagnostic(app_client, session_id, ALL_WRONG)

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json() == first.json()
    assert second.json()["diagnostic_score"] == 3

    rows = (await db_session.exec(select(SessionIntake))).all()
    assert len(rows) == 1
    assert rows[0].diagnostic_answers == ALL_CORRECT


async def test_diagnostic_falls_back_to_the_existing_row_when_the_insert_loses(
    app_client, db_session, monkeypatch
):
    """The race branch, simulated rather than observed.

    This forces the initial lookup to miss so the INSERT hits the real UNIQUE
    constraint. It does NOT reproduce genuine concurrency: the test fixture's
    single SQLite connection serializes writers, so the Postgres behaviour this
    branch relies on -- the losing INSERT blocking until the winner commits,
    making the row visible on re-fetch -- is not verified here.
    """

    session_id = await _start_session(app_client)
    winner = SessionIntake(
        session_id=UUID(session_id),
        diagnostic_answers=ALL_CORRECT,
        diagnostic_score=3,
        primer_shown=False,
    )
    db_session.add(winner)
    await db_session.commit()

    from api.services import intake as intake_service

    real_find = intake_service._find_intake
    calls = {"count": 0}

    async def _miss_once(session, *, session_id):
        calls["count"] += 1
        if calls["count"] == 1:
            return None
        return await real_find(session, session_id=session_id)

    monkeypatch.setattr(intake_service, "_find_intake", _miss_once)

    response = await _diagnostic(app_client, session_id, ALL_WRONG)

    assert response.status_code == 201
    # The winner's score survives, rather than being recomputed from the
    # losing submission's answers.
    assert response.json()["diagnostic_score"] == 3

    rows = (await db_session.exec(select(SessionIntake))).all()
    assert len(rows) == 1


@pytest.mark.parametrize(
    ("diagnostic_answers", "comprehension_answer", "expected_depth"),
    [
        (ALL_CORRECT, COMPREHENSION_ITEM.correct, ScaffoldingDepth.LOW),
        (ALL_CORRECT, WRONG_COMPREHENSION, ScaffoldingDepth.STANDARD),
        (ALL_WRONG, COMPREHENSION_ITEM.correct, ScaffoldingDepth.STANDARD),
        (ALL_WRONG, WRONG_COMPREHENSION, ScaffoldingDepth.HIGH),
    ],
)
async def test_comprehension_finalizes_a_scaffolding_depth(
    app_client, diagnostic_answers, comprehension_answer, expected_depth
):
    session_id = await _start_session(app_client)
    await _diagnostic(app_client, session_id, diagnostic_answers)

    response = await _comprehension(app_client, session_id, comprehension_answer)

    assert response.status_code == 201
    body = response.json()
    assert body["correct"] is (comprehension_answer == COMPREHENSION_ITEM.correct)
    assert body["scaffolding_depth"] == expected_depth.value


async def test_a_wrong_comprehension_answer_still_completes_the_intake(
    app_client, db_session
):
    """There is no second attempt: wrong finalizes exactly as right does."""

    session_id = await _start_session(app_client)
    await _diagnostic(app_client, session_id, ALL_CORRECT)

    response = await _comprehension(app_client, session_id, WRONG_COMPREHENSION)

    assert response.status_code == 201
    assert response.json()["correct"] is False

    row = (await db_session.exec(select(SessionIntake))).one()
    assert row.completed_at is not None
    assert row.scaffolding_depth is not None


async def test_comprehension_twice_returns_the_identical_result(app_client, db_session):
    session_id = await _start_session(app_client)
    await _diagnostic(app_client, session_id, ALL_CORRECT)

    first = await _comprehension(app_client, session_id, WRONG_COMPREHENSION)
    # A second, correct answer must not upgrade the stored outcome.
    second = await _comprehension(app_client, session_id, COMPREHENSION_ITEM.correct)

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json() == first.json()
    assert second.json()["correct"] is False

    row = (await db_session.exec(select(SessionIntake))).one()
    assert row.comprehension_answer == WRONG_COMPREHENSION


async def test_completed_at_is_not_restamped_by_a_repeat_call(app_client):
    session_id = await _start_session(app_client)
    await _diagnostic(app_client, session_id, ALL_CORRECT)
    await _comprehension(app_client, session_id, COMPREHENSION_ITEM.correct)

    first = await app_client.get(f"/sessions/{session_id}/intake")
    await _comprehension(app_client, session_id, COMPREHENSION_ITEM.correct)
    second = await app_client.get(f"/sessions/{session_id}/intake")

    assert _instant(first.json()["completed_at"]) == _instant(
        second.json()["completed_at"]
    )


async def test_comprehension_before_the_diagnostic_is_rejected(app_client):
    session_id = await _start_session(app_client)

    response = await _comprehension(app_client, session_id, COMPREHENSION_ITEM.correct)

    assert response.status_code == 409


async def test_unknown_option_ids_are_rejected(app_client):
    session_id = await _start_session(app_client)

    wrong_length = await _diagnostic(app_client, session_id, ALL_CORRECT[:2])
    assert wrong_length.status_code == 422

    unknown = await _diagnostic(app_client, session_id, ["nope", "nope", "nope"])
    assert unknown.status_code == 422


async def test_intake_state_round_trips_for_refresh_recovery(app_client):
    session_id = await _start_session(app_client)
    await _diagnostic(app_client, session_id, ONE_CORRECT)

    mid_flow = await app_client.get(f"/sessions/{session_id}/intake")

    assert mid_flow.status_code == 200
    body = mid_flow.json()
    assert body["diagnostic_score"] == 1
    assert body["diagnostic_answers"] == ONE_CORRECT
    assert body["comprehension_answer"] is None
    assert body["comprehension_correct"] is None
    assert body["scaffolding_depth"] is None
    assert body["completed_at"] is None

    await _comprehension(app_client, session_id, COMPREHENSION_ITEM.correct)
    finished = await app_client.get(f"/sessions/{session_id}/intake")

    assert finished.json()["comprehension_correct"] is True
    assert finished.json()["scaffolding_depth"] is not None
    assert finished.json()["completed_at"] is not None


async def test_intake_is_not_found_before_the_diagnostic(app_client):
    session_id = await _start_session(app_client)

    response = await app_client.get(f"/sessions/{session_id}/intake")

    assert response.status_code == 404


async def test_intake_responses_never_carry_the_answer_key(app_client):
    """No response may name a correct option id, at any step."""

    session_id = await _start_session(app_client)

    bodies = [
        (await _diagnostic(app_client, session_id, ALL_WRONG)).text,
        (await _comprehension(app_client, session_id, WRONG_COMPREHENSION)).text,
        (await app_client.get(f"/sessions/{session_id}/intake")).text,
    ]

    secrets = [item.correct for item in DIAGNOSTIC_ITEMS] + [COMPREHENSION_ITEM.correct]
    for body in bodies:
        for secret in secrets:
            assert secret not in body


async def test_another_learners_intake_is_not_found(app_client, learner):
    session_id = await _start_session(app_client)
    await _diagnostic(app_client, session_id, ALL_CORRECT)

    learner["id"] = uuid4()

    assert (await app_client.get(f"/sessions/{session_id}/intake")).status_code == 404
    assert (await _diagnostic(app_client, session_id, ALL_CORRECT)).status_code == 404
    assert (
        await _comprehension(app_client, session_id, COMPREHENSION_ITEM.correct)
    ).status_code == 404

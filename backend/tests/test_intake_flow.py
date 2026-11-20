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
    assert response.json()["diagnostic_score"] == expected_score


@pytest.mark.parametrize(
    ("correct_count", "expected_above"),
    [(DIAGNOSTIC_THRESHOLD - 1, False), (DIAGNOSTIC_THRESHOLD, True)],
)
async def test_a_score_at_the_threshold_counts_as_above_it(
    app_client, correct_count, expected_above
):
    session_id = await _start_session(app_client)
    answers = [*ALL_CORRECT[:correct_count], *ALL_WRONG[correct_count:]]

    response = await _diagnostic(app_client, session_id, answers)

    assert response.json()["above_threshold"] is expected_above


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


@pytest.mark.parametrize(
    (
        "diagnostic_answers",
        "comprehension_answer",
        "expected_correct",
        "expected_depth",
    ),
    [
        (ALL_CORRECT, COMPREHENSION_ITEM.correct, True, ScaffoldingDepth.LOW),
        (ALL_CORRECT, WRONG_COMPREHENSION, False, ScaffoldingDepth.STANDARD),
        (ALL_WRONG, COMPREHENSION_ITEM.correct, True, ScaffoldingDepth.STANDARD),
        (ALL_WRONG, WRONG_COMPREHENSION, False, ScaffoldingDepth.HIGH),
    ],
)
async def test_comprehension_finalizes_a_scaffolding_depth(
    app_client,
    diagnostic_answers,
    comprehension_answer,
    expected_correct,
    expected_depth,
):
    session_id = await _start_session(app_client)
    await _diagnostic(app_client, session_id, diagnostic_answers)

    response = await _comprehension(app_client, session_id, comprehension_answer)

    assert response.status_code == 201
    body = response.json()
    assert body["correct"] is expected_correct
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


async def test_each_correct_option_is_returned_only_after_its_answer_is_stored(
    app_client,
):
    session_id = await _start_session(app_client)
    diagnostic_key = [item.correct for item in DIAGNOSTIC_ITEMS]

    diagnostic = await _diagnostic(app_client, session_id, ALL_WRONG)
    before_comprehension = await app_client.get(f"/sessions/{session_id}/intake")

    assert diagnostic.json()["correct_answers"] == diagnostic_key
    assert COMPREHENSION_ITEM.correct not in diagnostic.text
    assert COMPREHENSION_ITEM.correct not in before_comprehension.text

    # Knowing the key no longer changes the stored score.
    resubmitted = await _diagnostic(app_client, session_id, diagnostic_key)
    assert resubmitted.json()["diagnostic_score"] == 0

    comprehension = await _comprehension(app_client, session_id, WRONG_COMPREHENSION)
    assert comprehension.json()["correct_answer"] == COMPREHENSION_ITEM.correct
    finished = (await app_client.get(f"/sessions/{session_id}/intake")).json()
    assert finished["comprehension_correct_answer"] == COMPREHENSION_ITEM.correct

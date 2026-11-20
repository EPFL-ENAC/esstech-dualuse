"""M0 intake: three diagnostic items, a primer, one comprehension check.

The answer key lives in api/content/intake_key.py. An item's correct option
is returned only once the learner's answer to it is stored, so it can be shown
as feedback but never used to change an answer.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import update
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.content.intake_key import (
    COMPREHENSION_ITEM,
    DIAGNOSTIC_ITEMS,
    derive_scaffolding_depth,
    is_above_threshold,
    is_comprehension_correct,
    score_diagnostic,
)
from api.models import SessionIntake
from api.models.base import utc_now
from api.models.enums import ScaffoldingDepth
from api.services.errors import ConflictError, NotFoundError, ValidationError
from api.services.persistence import insert_once


class DiagnosticSubmission(BaseModel):
    """Request body for the three diagnostic items, in item order."""

    answers: list[str]


class DiagnosticResult(BaseModel):
    """The diagnostic outcome, with each item's correct option in item order."""

    diagnostic_score: int
    above_threshold: bool
    correct_answers: list[str]


class ComprehensionSubmission(BaseModel):
    """Request body for the single comprehension item."""

    answer: str


class ComprehensionResult(BaseModel):
    """The comprehension outcome, and the depth it finalized."""

    correct: bool
    correct_answer: str
    scaffolding_depth: ScaffoldingDepth


class IntakeState(BaseModel):
    """The full stored intake, for recovering an interrupted flow."""

    session_id: UUID
    diagnostic_answers: list[str]
    diagnostic_score: int
    above_threshold: bool
    diagnostic_correct_answers: list[str]
    primer_shown: bool
    created_at: datetime
    comprehension_answer: str | None
    comprehension_correct: bool | None
    comprehension_correct_answer: str | None
    scaffolding_depth: ScaffoldingDepth | None
    completed_at: datetime | None


DIAGNOSTIC_CORRECT_ANSWERS = [item.correct for item in DIAGNOSTIC_ITEMS]


def _to_state(record: SessionIntake) -> IntakeState:
    return IntakeState(
        session_id=record.session_id,
        diagnostic_answers=record.diagnostic_answers,
        diagnostic_score=record.diagnostic_score,
        above_threshold=is_above_threshold(record.diagnostic_score),
        diagnostic_correct_answers=DIAGNOSTIC_CORRECT_ANSWERS,
        primer_shown=record.primer_shown,
        created_at=record.created_at,
        comprehension_answer=record.comprehension_answer,
        comprehension_correct=(
            None
            if record.comprehension_answer is None
            else is_comprehension_correct(record.comprehension_answer)
        ),
        comprehension_correct_answer=(
            None if record.comprehension_answer is None else COMPREHENSION_ITEM.correct
        ),
        scaffolding_depth=record.scaffolding_depth,
        completed_at=record.completed_at,
    )


async def _find_intake(
    session: AsyncSession, *, session_id: UUID
) -> SessionIntake | None:
    return (
        await session.exec(
            select(SessionIntake).where(SessionIntake.session_id == session_id)
        )
    ).first()


async def submit_diagnostic(
    session: AsyncSession, *, session_id: UUID, answers: list[str]
) -> DiagnosticResult:
    """Score the diagnostic once, then return that same score forever after.

    A racing insert loses to the UNIQUE constraint on session_id rather than
    overwriting a score the learner has already seen.
    """

    existing = await _find_intake(session, session_id=session_id)
    if existing is not None:
        return _diagnostic_result(existing)

    _validate_diagnostic(answers)

    score = score_diagnostic(answers)
    record, created = await insert_once(
        session,
        SessionIntake(
            session_id=session_id,
            diagnostic_answers=answers,
            diagnostic_score=score,
            primer_shown=not is_above_threshold(score),
        ),
        lambda: _find_intake(session, session_id=session_id),
    )
    if created:
        await session.commit()

    return _diagnostic_result(record)


def _diagnostic_result(record: SessionIntake) -> DiagnosticResult:
    return DiagnosticResult(
        diagnostic_score=record.diagnostic_score,
        above_threshold=is_above_threshold(record.diagnostic_score),
        correct_answers=DIAGNOSTIC_CORRECT_ANSWERS,
    )


def _validate_diagnostic(answers: list[str]) -> None:
    if len(answers) != len(DIAGNOSTIC_ITEMS):
        raise ValidationError(
            f"Expected {len(DIAGNOSTIC_ITEMS)} answers, got {len(answers)}"
        )
    for item, answer in zip(DIAGNOSTIC_ITEMS, answers, strict=True):
        if answer not in item.options:
            raise ValidationError(f"Unknown option for item {item.id}")


async def submit_comprehension(
    session: AsyncSession, *, session_id: UUID, answer: str
) -> ComprehensionResult:
    """Finalize the intake, whether the answer is right or wrong.

    There is no second attempt: a wrong answer means the frontend shows static
    correction content and moves on.
    """

    record = await _find_intake(session, session_id=session_id)
    if record is None:
        raise ConflictError(
            "Diagnostic must be submitted before the comprehension check"
        )

    if record.completed_at is not None:
        return _completed_result(record)

    if answer not in COMPREHENSION_ITEM.options:
        raise ValidationError(f"Unknown option for item {COMPREHENSION_ITEM.id}")

    correct = is_comprehension_correct(answer)
    depth = derive_scaffolding_depth(
        above_threshold=is_above_threshold(record.diagnostic_score),
        comprehension_correct=correct,
    )

    result = await session.exec(
        update(SessionIntake)
        .where(
            col(SessionIntake.session_id) == session_id,
            col(SessionIntake.completed_at).is_(None),
        )
        .values(
            comprehension_answer=answer,
            scaffolding_depth=depth,
            completed_at=utc_now(),
        )
    )
    await session.commit()

    if result.rowcount == 0:
        # A concurrent submission finalized first. Its stored outcome stands.
        winner = await _find_intake(session, session_id=session_id)
        if winner is None or winner.completed_at is None:
            raise ConflictError("Intake could not be finalized")
        return _completed_result(winner)

    return ComprehensionResult(
        correct=correct,
        correct_answer=COMPREHENSION_ITEM.correct,
        scaffolding_depth=depth,
    )


def _completed_result(record: SessionIntake) -> ComprehensionResult:
    """Rebuild the outcome of an already-finalized intake from its row."""

    if record.scaffolding_depth is None:
        raise ConflictError("Intake is finished but has no scaffolding depth")

    return ComprehensionResult(
        correct=is_comprehension_correct(record.comprehension_answer),
        correct_answer=COMPREHENSION_ITEM.correct,
        scaffolding_depth=record.scaffolding_depth,
    )


async def get_intake(session: AsyncSession, *, session_id: UUID) -> IntakeState:
    """Return the stored intake, so a reloaded page can resume mid-flow."""

    record = await _find_intake(session, session_id=session_id)
    if record is None:
        raise NotFoundError("Intake not found")

    return _to_state(record)

"""M0 intake: three diagnostic items, a primer, one comprehension check.

Every response here reports an *outcome* -- a score, a boolean, a depth --
and never which option was correct. The answer key lives in
api/content/intake_key.py and stays there.
"""

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.content.intake_key import (
    COMPREHENSION_ITEM,
    DIAGNOSTIC_ITEMS,
    DIAGNOSTIC_THRESHOLD,
    derive_scaffolding_depth,
    score_diagnostic,
)
from api.models import SessionIntake
from api.models.enums import ScaffoldingDepth
from api.services.errors import ConflictError, NotFoundError, ServiceError
from api.services.sessions import get_owned_session


class DiagnosticSubmission(BaseModel):
    """Request body for the three diagnostic items, in item order."""

    answers: list[str]


class DiagnosticResult(BaseModel):
    """The diagnostic outcome. Carries no answer key."""

    diagnostic_score: int
    above_threshold: bool


class ComprehensionSubmission(BaseModel):
    """Request body for the single comprehension item."""

    answer: str


class ComprehensionResult(BaseModel):
    """The comprehension outcome, and the depth it finalized."""

    correct: bool
    scaffolding_depth: ScaffoldingDepth


class IntakeState(BaseModel):
    """The full stored intake, for recovering an interrupted flow.

    `comprehension_correct` reports whether the learner's own stored answer was
    right. That is not an oracle for the answer key: the flow is one-shot, so
    there is no way to resubmit a different option and watch the boolean move.
    """

    session_id: UUID
    diagnostic_answers: list[str]
    diagnostic_score: int
    above_threshold: bool
    primer_shown: bool
    created_at: datetime
    comprehension_answer: str | None
    comprehension_correct: bool | None
    scaffolding_depth: ScaffoldingDepth | None
    completed_at: datetime | None


class ValidationError(ServiceError):
    """The submission does not match the item set it claims to answer."""

    status_code = 422


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _above_threshold(score: int) -> bool:
    return score >= DIAGNOSTIC_THRESHOLD


def _to_state(record: SessionIntake) -> IntakeState:
    return IntakeState(
        session_id=record.session_id,
        diagnostic_answers=record.diagnostic_answers,
        diagnostic_score=record.diagnostic_score,
        above_threshold=_above_threshold(record.diagnostic_score),
        primer_shown=record.primer_shown,
        created_at=record.created_at,
        comprehension_answer=record.comprehension_answer,
        comprehension_correct=(
            None
            if record.comprehension_answer is None
            else record.comprehension_answer == COMPREHENSION_ITEM.correct
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
    session: AsyncSession, *, session_id: UUID, learner_id: UUID, answers: list[str]
) -> DiagnosticResult:
    """Score the diagnostic once, then return that same score forever after.

    Idempotent the way the reveal is (api/services/feedback.py): an existing
    row short-circuits, and a racing insert loses to the UNIQUE constraint on
    session_id rather than overwriting a score the learner has already seen.
    """

    await get_owned_session(session, session_id=session_id, learner_id=learner_id)

    existing = await _find_intake(session, session_id=session_id)
    if existing is not None:
        return DiagnosticResult(
            diagnostic_score=existing.diagnostic_score,
            above_threshold=_above_threshold(existing.diagnostic_score),
        )

    _validate_diagnostic(answers)

    score = score_diagnostic(answers)
    above = _above_threshold(score)
    record = SessionIntake(
        session_id=session_id,
        diagnostic_answers=answers,
        diagnostic_score=score,
        # No endpoint reports this, so it is derived: the primer is shown to
        # exactly those learners who scored below the threshold.
        primer_shown=not above,
    )
    session.add(record)
    try:
        await session.flush()
    except IntegrityError:
        # A concurrent submission inserted first. Roll back before querying:
        # the session cannot run further statements while the failed
        # transaction is open.
        await session.rollback()
        existing = await _find_intake(session, session_id=session_id)
        if existing is None:
            # Not the unique violation we expected, so this is a real fault.
            raise
        return DiagnosticResult(
            diagnostic_score=existing.diagnostic_score,
            above_threshold=_above_threshold(existing.diagnostic_score),
        )
    await session.commit()

    return DiagnosticResult(diagnostic_score=score, above_threshold=above)


def _validate_diagnostic(answers: list[str]) -> None:
    if len(answers) != len(DIAGNOSTIC_ITEMS):
        raise ValidationError(
            f"Expected {len(DIAGNOSTIC_ITEMS)} answers, got {len(answers)}"
        )
    for item, answer in zip(DIAGNOSTIC_ITEMS, answers, strict=True):
        if answer not in item.options:
            raise ValidationError(f"Unknown option for item {item.id}")


async def submit_comprehension(
    session: AsyncSession, *, session_id: UUID, learner_id: UUID, answer: str
) -> ComprehensionResult:
    """Finalize the intake, whether the answer is right or wrong.

    There is no second attempt: a wrong answer means the frontend shows static
    correction content and moves on, so this call always stamps
    scaffolding_depth and completed_at.

    The reveal's insert-and-catch does not transfer here -- the row already
    exists, so this is an UPDATE. The equivalent database-level guard is the
    `completed_at IS NULL` predicate: a second caller updates zero rows and
    reads back whatever the winner stored.
    """

    await get_owned_session(session, session_id=session_id, learner_id=learner_id)

    record = await _find_intake(session, session_id=session_id)
    if record is None:
        raise ConflictError(
            "Diagnostic must be submitted before the comprehension check"
        )

    if record.completed_at is not None:
        return _completed_result(record)

    if answer not in COMPREHENSION_ITEM.options:
        raise ValidationError(f"Unknown option for item {COMPREHENSION_ITEM.id}")

    correct = answer == COMPREHENSION_ITEM.correct
    depth = derive_scaffolding_depth(
        above_threshold=_above_threshold(record.diagnostic_score),
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
            completed_at=_utc_now(),
        )
    )
    await session.commit()

    if result.rowcount == 0:
        # A concurrent submission finalized first. Its stored outcome stands.
        winner = await _find_intake(session, session_id=session_id)
        if winner is None or winner.completed_at is None:
            raise ConflictError("Intake could not be finalized")
        return _completed_result(winner)

    return ComprehensionResult(correct=correct, scaffolding_depth=depth)


def _completed_result(record: SessionIntake) -> ComprehensionResult:
    """Rebuild the outcome of an already-finalized intake from its row."""

    if record.scaffolding_depth is None:
        # completed_at and scaffolding_depth are written in the same UPDATE, so
        # one without the other means the row was tampered with out of band.
        raise ConflictError("Intake is finished but has no scaffolding depth")

    return ComprehensionResult(
        correct=record.comprehension_answer == COMPREHENSION_ITEM.correct,
        scaffolding_depth=record.scaffolding_depth,
    )


async def get_intake(
    session: AsyncSession, *, session_id: UUID, learner_id: UUID
) -> IntakeState:
    """Return the stored intake, so a reloaded page can resume mid-flow."""

    await get_owned_session(session, session_id=session_id, learner_id=learner_id)

    record = await _find_intake(session, session_id=session_id)
    if record is None:
        raise NotFoundError("Intake not found")

    return _to_state(record)

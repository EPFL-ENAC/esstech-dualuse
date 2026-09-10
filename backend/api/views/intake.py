from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.db import get_db_session
from api.dependencies import get_current_learner
from api.services.intake import (
    ComprehensionResult,
    ComprehensionSubmission,
    DiagnosticResult,
    DiagnosticSubmission,
    IntakeState,
    get_intake,
    submit_comprehension,
    submit_diagnostic,
)

router = APIRouter()


@router.post(
    "/sessions/{session_id}/intake/diagnostic",
    response_model=DiagnosticResult,
    status_code=status.HTTP_201_CREATED,
    summary="Submit the diagnostic items",
    description=(
        "Score the three diagnostic items and decide whether the micro-primer "
        "is shown. Scored once, then returned unchanged on every later call. "
        "The response reports the score and the threshold comparison, never "
        "which option was correct."
    ),
    tags=["Intake"],
)
async def post_diagnostic(
    session_id: UUID,
    body: DiagnosticSubmission,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> DiagnosticResult:
    return await submit_diagnostic(
        session,
        session_id=session_id,
        learner_id=learner_id,
        answers=body.answers,
    )


@router.post(
    "/sessions/{session_id}/intake/comprehension",
    response_model=ComprehensionResult,
    status_code=status.HTTP_201_CREATED,
    summary="Submit the comprehension check",
    description=(
        "Finalize the intake and its scaffolding depth. There is no second "
        "attempt: a wrong answer finalizes just as a right one does, and every "
        "later call returns the same stored outcome."
    ),
    tags=["Intake"],
)
async def post_comprehension(
    session_id: UUID,
    body: ComprehensionSubmission,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> ComprehensionResult:
    return await submit_comprehension(
        session,
        session_id=session_id,
        learner_id=learner_id,
        answer=body.answer,
    )


@router.get(
    "/sessions/{session_id}/intake",
    response_model=IntakeState,
    summary="Read the intake state",
    description=(
        "Return this session's stored intake so a reloaded page can resume mid-flow."
    ),
    tags=["Intake"],
)
async def get_session_intake(
    session_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> IntakeState:
    return await get_intake(session, session_id=session_id, learner_id=learner_id)

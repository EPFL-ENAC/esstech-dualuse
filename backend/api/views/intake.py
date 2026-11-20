from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.db import get_db_session
from api.dependencies import get_student_session
from api.models import Session
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

router = APIRouter(tags=["Intake"])


@router.post(
    "/sessions/{session_id}/intake/diagnostic",
    response_model=DiagnosticResult,
    status_code=status.HTTP_201_CREATED,
    summary="Submit the diagnostic items",
    description=(
        "Score the three diagnostic items and decide whether the micro-primer "
        "is shown. Scored once, then returned unchanged on every later call. "
        "The response carries the score, the threshold comparison and each "
        "item's correct option, which can no longer change the stored score."
    ),
)
async def post_diagnostic(
    body: DiagnosticSubmission,
    owned: Session = Depends(get_student_session),
    session: AsyncSession = Depends(get_db_session),
) -> DiagnosticResult:
    return await submit_diagnostic(
        session,
        session_id=owned.id,
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
)
async def post_comprehension(
    body: ComprehensionSubmission,
    owned: Session = Depends(get_student_session),
    session: AsyncSession = Depends(get_db_session),
) -> ComprehensionResult:
    return await submit_comprehension(
        session,
        session_id=owned.id,
        answer=body.answer,
    )


@router.get(
    "/sessions/{session_id}/intake",
    response_model=IntakeState,
    summary="Read the intake state",
    description=(
        "Return this session's stored intake so a reloaded page can resume mid-flow."
    ),
)
async def get_session_intake(
    owned: Session = Depends(get_student_session),
    session: AsyncSession = Depends(get_db_session),
) -> IntakeState:
    return await get_intake(session, session_id=owned.id)

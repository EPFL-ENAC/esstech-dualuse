from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.db import get_db_session
from api.dependencies import get_current_learner
from api.services.encounters import EncounterCreate, EncounterCreated, create_encounter
from api.services.report import SessionReport, get_session_report
from api.services.sessions import SessionCreated, create_session

router = APIRouter()


@router.post(
    "/sessions",
    response_model=SessionCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Start a session",
    description="Start a student/individual session for the current learner.",
    tags=["Sessions"],
)
async def post_session(
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> SessionCreated:
    return await create_session(session, learner_id=learner_id)


@router.post(
    "/sessions/{session_id}/encounters",
    response_model=EncounterCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Select a case",
    description=(
        "Add a case to this session as its next encounter. The response "
        "excludes the case's full narrative and main path."
    ),
    tags=["Sessions"],
)
async def post_encounter(
    session_id: UUID,
    body: EncounterCreate,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> EncounterCreated:
    return await create_encounter(
        session,
        session_id=session_id,
        learner_id=learner_id,
        case_id=body.case_id,
    )


@router.get(
    "/sessions/{session_id}/report",
    response_model=SessionReport,
    response_model_exclude_none=True,
    summary="Get the session's reflection report",
    description=(
        "The M6/M7 self-reflection debrief: a read-only aggregation over "
        "the session's completed encounters. Minimal when no case has been "
        "completed yet, rather than empty lists or zeroed counts."
    ),
    tags=["Sessions"],
)
async def get_session_report_endpoint(
    session_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> SessionReport:
    return await get_session_report(
        session, session_id=session_id, learner_id=learner_id
    )

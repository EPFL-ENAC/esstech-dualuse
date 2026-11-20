from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.db import get_db_session
from api.dependencies import get_current_learner, get_student_session
from api.models import Session
from api.services.encounters import EncounterCreate, EncounterCreated, create_encounter
from api.services.report import SessionReport, get_session_report
from api.services.sessions import SessionCreate, SessionCreated, create_session

router = APIRouter(tags=["Sessions"])


@router.post(
    "/sessions",
    response_model=SessionCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Start a session",
    description=(
        "Start an individual session for the current learner. Defaults to "
        "the Student route when the body is omitted or route is not set."
    ),
)
async def post_session(
    body: SessionCreate | None = None,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> SessionCreated:
    route = (body or SessionCreate()).route
    return await create_session(session, learner_id=learner_id, route=route)


@router.post(
    "/sessions/{session_id}/encounters",
    response_model=EncounterCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Select a case",
    description=(
        "Add a case to this session as its next encounter. The response "
        "excludes the case's full narrative and main path."
    ),
)
async def post_encounter(
    body: EncounterCreate,
    owned: Session = Depends(get_student_session),
    session: AsyncSession = Depends(get_db_session),
) -> EncounterCreated:
    return await create_encounter(session, session_id=owned.id, case_id=body.case_id)


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
)
async def get_session_report_endpoint(
    owned: Session = Depends(get_student_session),
    session: AsyncSession = Depends(get_db_session),
) -> SessionReport:
    return await get_session_report(session, session_id=owned.id)

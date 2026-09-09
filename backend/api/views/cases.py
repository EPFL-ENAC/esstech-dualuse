from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from api.db import get_db_session
from api.dependencies import get_current_learner
from api.services.cases import CaseCandidate, list_candidate_cases

router = APIRouter()


@router.get(
    "/cases/candidates",
    response_model=list[CaseCandidate],
    summary="List candidate cases",
    description=(
        "Up to three published harm cases the current learner has not yet "
        "encountered in any session. The response excludes each case's full "
        "narrative and main path."
    ),
    tags=["Cases"],
)
async def get_case_candidates(
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> list[CaseCandidate]:
    return await list_candidate_cases(session, learner_id=learner_id)

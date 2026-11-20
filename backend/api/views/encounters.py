from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.db import get_db_session
from api.dependencies import get_student_encounter
from api.models import CaseEncounter
from api.services.contrast import (
    ContrastResponse,
    ContrastSubmit,
    CounterCaseResponse,
    look_up_counter_case,
    submit_contrast,
)
from api.services.encounters import (
    CommitmentCreate,
    CommitmentCreated,
    create_commitment,
)
from api.services.feedback import RevealResponse, reveal_encounter

router = APIRouter(tags=["Encounters"])


@router.post(
    "/encounters/{encounter_id}/commitments",
    response_model=CommitmentCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Commit to an interpretation",
    description=(
        "Store the learner's framing answers and their chosen pattern and "
        "gate for this encounter."
    ),
)
async def post_commitment(
    body: CommitmentCreate,
    encounter: CaseEncounter = Depends(get_student_encounter),
    session: AsyncSession = Depends(get_db_session),
) -> CommitmentCreated:
    return await create_commitment(
        session,
        encounter=encounter,
        pattern=body.pattern,
        gate=body.gate,
        framing_answers=body.framing_answers,
    )


@router.post(
    "/encounters/{encounter_id}/reveal",
    response_model=RevealResponse,
    summary="Reveal the case",
    description=(
        "Return the case's full narrative and main path alongside how the "
        "learner's commitment compared. Computed once, then returned "
        "unchanged on every later call."
    ),
)
async def post_reveal(
    encounter: CaseEncounter = Depends(get_student_encounter),
    session: AsyncSession = Depends(get_db_session),
) -> RevealResponse:
    return await reveal_encounter(session, encounter=encounter)


@router.get(
    "/encounters/{encounter_id}/counter-case",
    response_model=CounterCaseResponse,
    summary="Look up the encounter's counter-case",
    description=(
        "Report whether this encounter's case has a linked counter-case, and "
        "if so, the gate lever and responsibility-posture contrast to show "
        "before the reflection question."
    ),
)
async def get_counter_case(
    encounter: CaseEncounter = Depends(get_student_encounter),
    session: AsyncSession = Depends(get_db_session),
) -> CounterCaseResponse:
    return await look_up_counter_case(session, encounter=encounter)


@router.post(
    "/encounters/{encounter_id}/contrast",
    response_model=ContrastResponse,
    summary="Submit the post-reveal contrast reflection",
    description=(
        "Record the learner's twin-counter-case reflection, or the open-area "
        "acknowledgement when no counter-case exists. The contrast type and "
        "counter-case id are derived server-side, never trusted from the "
        "request. Computed once, then returned unchanged on every later call."
    ),
)
async def post_contrast(
    body: ContrastSubmit,
    encounter: CaseEncounter = Depends(get_student_encounter),
    session: AsyncSession = Depends(get_db_session),
) -> ContrastResponse:
    return await submit_contrast(
        session,
        encounter=encounter,
        learner_response=body.learner_response,
    )

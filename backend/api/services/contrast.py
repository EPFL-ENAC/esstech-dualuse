from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import ContrastEntry, CounterCaseLink
from api.models.enums import ContrastType, Gate
from api.services.encounters import get_owned_encounter
from api.services.errors import ValidationError
from api.services.sessions import get_owned_session, require_student_route


class CounterCaseInfo(BaseModel):
    """The counter-case fields shown before the WHO reflection question."""

    counter_case_id: UUID
    gate_lever: Gate
    responsibility_posture_contrast: str


class CounterCaseResponse(BaseModel):
    """Whether this encounter's case has a linked counter-case."""

    has_counter_case: bool
    counter_case: CounterCaseInfo | None


class ContrastSubmit(BaseModel):
    """Request body for the post-reveal contrast reflection."""

    learner_response: str | None = None


class ContrastResponse(BaseModel):
    """The stored contrast entry, whichever branch produced it."""

    contrast_entry_id: UUID
    contrast_type: ContrastType
    counter_case_id: UUID | None
    learner_response: str | None
    created_at: datetime


async def find_counter_case_link(
    session: AsyncSession, *, case_id: UUID
) -> CounterCaseLink | None:
    return (
        await session.exec(
            select(CounterCaseLink).where(CounterCaseLink.harm_case_id == case_id)
        )
    ).first()


async def _find_contrast_entry(
    session: AsyncSession, *, encounter_id: UUID
) -> ContrastEntry | None:
    return (
        await session.exec(
            select(ContrastEntry).where(ContrastEntry.case_encounter_id == encounter_id)
        )
    ).first()


def _respond(entry: ContrastEntry) -> ContrastResponse:
    return ContrastResponse(
        contrast_entry_id=entry.id,
        contrast_type=entry.contrast_type,
        counter_case_id=entry.counter_case_id,
        learner_response=entry.learner_response,
        created_at=entry.created_at,
    )


async def look_up_counter_case(
    session: AsyncSession, *, encounter_id: UUID, learner_id: UUID
) -> CounterCaseResponse:
    """Report the counter-case linked to this encounter's case, if any.

    A case with no counter-case is a valid corpus state, not an error: this
    never 404s for that reason, only for an ownership mismatch.
    """

    encounter = await get_owned_encounter(
        session, encounter_id=encounter_id, learner_id=learner_id
    )
    owned_session = await get_owned_session(
        session, session_id=encounter.session_id, learner_id=learner_id
    )
    require_student_route(owned_session.route)

    link = await find_counter_case_link(session, case_id=encounter.case_id)
    if link is None:
        return CounterCaseResponse(has_counter_case=False, counter_case=None)

    return CounterCaseResponse(
        has_counter_case=True,
        counter_case=CounterCaseInfo(
            counter_case_id=link.counter_case_id,
            gate_lever=link.gate_lever,
            responsibility_posture_contrast=link.responsibility_posture_contrast,
        ),
    )


async def submit_contrast(
    session: AsyncSession,
    *,
    encounter_id: UUID,
    learner_id: UUID,
    learner_response: str | None,
) -> ContrastResponse:
    """Record the encounter's contrast reflection, computing it only the first time.

    contrast_type and counter_case_id are derived here from the encounter's own
    case, never from the request. A non-empty learner_response is required when
    a counter-case exists -- that question is the pedagogical core of the twin
    branch, not decoration -- and is always discarded (forced to None) for the
    open-area branch, which asks nothing. Idempotent the way reveal_encounter is
    (api/services/feedback.py).
    """

    encounter = await get_owned_encounter(
        session, encounter_id=encounter_id, learner_id=learner_id
    )
    owned_session = await get_owned_session(
        session, session_id=encounter.session_id, learner_id=learner_id
    )
    require_student_route(owned_session.route)

    existing = await _find_contrast_entry(session, encounter_id=encounter_id)
    if existing is not None:
        return _respond(existing)

    link = await find_counter_case_link(session, case_id=encounter.case_id)
    if link is not None:
        if not (learner_response and learner_response.strip()):
            raise ValidationError("A reflection response is required")
        contrast_type = ContrastType.TWIN_COUNTER_CASE
        counter_case_id = link.counter_case_id
        learner_response = learner_response.strip()
    else:
        contrast_type = ContrastType.OPEN_AREA
        counter_case_id = None
        learner_response = None

    record = ContrastEntry(
        case_encounter_id=encounter_id,
        contrast_type=contrast_type,
        counter_case_id=counter_case_id,
        learner_response=learner_response,
    )
    session.add(record)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        existing = await _find_contrast_entry(session, encounter_id=encounter_id)
        if existing is None:
            raise
        return _respond(existing)
    await session.commit()

    return _respond(record)

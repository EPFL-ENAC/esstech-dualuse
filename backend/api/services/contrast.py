from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import CaseEncounter, ContrastEntry, CounterCaseLink
from api.models.enums import ContrastType, Gate
from api.services.errors import ValidationError
from api.services.persistence import insert_once


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
    session: AsyncSession, *, case_ids: list[UUID]
) -> CounterCaseLink | None:
    """The counter-case link of the first of `case_ids` that is a linked harm
    case, in a stable order."""

    if not case_ids:
        return None

    return (
        await session.exec(
            select(CounterCaseLink)
            .where(col(CounterCaseLink.harm_case_id).in_(case_ids))
            .order_by(col(CounterCaseLink.harm_case_id), col(CounterCaseLink.id))
        )
    ).first()


def counter_case_response(link: CounterCaseLink | None) -> CounterCaseResponse:
    """A case or set with no counter-case is a valid corpus state, not an error."""

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


def resolve_contrast(
    link: CounterCaseLink | None, learner_response: str | None
) -> tuple[ContrastType, str | None]:
    """Derive the contrast branch from the corpus, never from the request.

    The twin branch requires a reflection -- that question is its pedagogical
    core. The open-area branch asks nothing, so any response is discarded.
    """

    if link is None:
        return ContrastType.OPEN_AREA, None
    if not (learner_response and learner_response.strip()):
        raise ValidationError("A reflection response is required")
    return ContrastType.TWIN_COUNTER_CASE, learner_response.strip()


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
    session: AsyncSession, *, encounter: CaseEncounter
) -> CounterCaseResponse:
    link = await find_counter_case_link(session, case_ids=[encounter.case_id])
    return counter_case_response(link)


async def submit_contrast(
    session: AsyncSession,
    *,
    encounter: CaseEncounter,
    learner_response: str | None,
) -> ContrastResponse:
    """Record the encounter's contrast reflection, computing it only the first time."""

    encounter_id = encounter.id

    existing = await _find_contrast_entry(session, encounter_id=encounter_id)
    if existing is not None:
        return _respond(existing)

    link = await find_counter_case_link(session, case_ids=[encounter.case_id])
    contrast_type, learner_response = resolve_contrast(link, learner_response)
    counter_case_id = link.counter_case_id if link is not None else None

    record, created = await insert_once(
        session,
        ContrastEntry(
            case_encounter_id=encounter_id,
            contrast_type=contrast_type,
            counter_case_id=counter_case_id,
            learner_response=learner_response,
        ),
        lambda: _find_contrast_entry(session, encounter_id=encounter_id),
    )
    if created:
        await session.commit()

    return _respond(record)

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Case, CaseEncounter, Commitment, Session
from api.models.enums import Gate, Pattern, SessionRoute
from api.models.session import MAX_ENCOUNTERS_PER_SESSION
from api.services.cases import CaseCandidate, offerable_cases, to_candidate
from api.services.errors import ConflictError, NotFoundError
from api.services.persistence import insert_once
from api.services.sessions import require_route


class EncounterCreate(BaseModel):
    """Request body for selecting a case to work through."""

    case_id: UUID


class EncounterCreated(BaseModel):
    """A case selected into a session, still without any spoiler fields."""

    id: UUID
    session_id: UUID
    sequence_no: int
    created_at: datetime
    case: CaseCandidate


class CommitmentCreate(BaseModel):
    """Request body for committing to an interpretation."""

    pattern: Pattern
    gate: Gate
    framing_answers: dict[str, Any] = Field(default_factory=dict)


class CommitmentCreated(BaseModel):
    """A stored commitment. Carries no verdict -- that is the reveal's job."""

    id: UUID
    case_encounter_id: UUID
    sequence_no: int
    pattern: Pattern
    gate: Gate
    framing_answers: dict[str, Any]
    created_at: datetime


async def get_owned_encounter(
    session: AsyncSession, *, encounter_id: UUID, learner_id: UUID
) -> CaseEncounter:
    """Load an encounter, treating another learner's encounter as nonexistent.

    Encounters exist only on the Student route, so a session of the other
    route is rejected here too.
    """

    row = (
        await session.exec(
            select(CaseEncounter, Session)
            .join(Session, onclause=col(Session.id) == col(CaseEncounter.session_id))
            .where(
                col(CaseEncounter.id) == encounter_id,
                Session.learner_id == learner_id,
            )
        )
    ).first()
    if row is None:
        raise NotFoundError("Encounter not found")

    encounter, owner = row
    require_route(owner.route, SessionRoute.STUDENT)
    return encounter


async def create_encounter(
    session: AsyncSession, *, session_id: UUID, case_id: UUID
) -> EncounterCreated:
    """Select a case into a session as its next encounter."""

    case = (
        await session.exec(select(Case).where(Case.id == case_id, *offerable_cases()))
    ).first()
    if case is None:
        raise NotFoundError("Case not found")

    existing = (
        await session.exec(
            select(CaseEncounter).where(CaseEncounter.session_id == session_id)
        )
    ).all()
    if any(encounter.case_id == case_id for encounter in existing):
        raise ConflictError("Case already selected in this session")
    if len(existing) >= MAX_ENCOUNTERS_PER_SESSION:
        raise ConflictError("Session cannot accept another encounter")

    record = CaseEncounter(
        session_id=session_id, case_id=case_id, sequence_no=len(existing) + 1
    )
    session.add(record)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        # A concurrent request claimed this sequence_no first; the
        # (session_id, sequence_no) UNIQUE constraint settles the race.
        raise ConflictError("Session cannot accept another encounter") from exc
    await session.commit()

    return EncounterCreated(
        id=record.id,
        session_id=record.session_id,
        sequence_no=record.sequence_no,
        created_at=record.created_at,
        case=to_candidate(case),
    )


async def create_commitment(
    session: AsyncSession,
    *,
    encounter: CaseEncounter,
    pattern: Pattern,
    gate: Gate,
    framing_answers: dict[str, Any],
) -> CommitmentCreated:
    """Store the learner's interpretation of an encounter.

    One commitment per encounter for now. `Commitment` is keyed on
    (case_encounter_id, sequence_no) so a future group re-vote can add a
    second row without overwriting the first.
    """

    encounter_id = encounter.id

    async def find_existing() -> Commitment | None:
        return (
            await session.exec(
                select(Commitment).where(Commitment.case_encounter_id == encounter_id)
            )
        ).first()

    record, created = await insert_once(
        session,
        Commitment(
            case_encounter_id=encounter_id,
            sequence_no=1,
            pattern=pattern,
            gate=gate,
            framing_answers=framing_answers,
        ),
        find_existing,
    )
    if not created:
        raise ConflictError("Encounter already has a commitment")
    await session.commit()

    return CommitmentCreated(
        id=record.id,
        case_encounter_id=record.case_encounter_id,
        sequence_no=record.sequence_no,
        pattern=record.pattern,
        gate=record.gate,
        framing_answers=record.framing_answers,
        created_at=record.created_at,
    )

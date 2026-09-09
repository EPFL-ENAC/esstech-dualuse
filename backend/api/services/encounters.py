from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Case, CaseEncounter, Commitment, Session
from api.models.enums import CaseStatus, CaseType, Gate, Pattern
from api.services.cases import CaseCandidate, to_candidate
from api.services.errors import ConflictError, NotFoundError
from api.services.sessions import get_owned_session


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
    """Load an encounter, treating another learner's encounter as nonexistent."""

    record = (
        await session.exec(
            select(CaseEncounter)
            .join(Session, onclause=col(Session.id) == col(CaseEncounter.session_id))
            .where(
                col(CaseEncounter.id) == encounter_id,
                Session.learner_id == learner_id,
            )
        )
    ).first()
    if record is None:
        raise NotFoundError("Encounter not found")

    return record


async def create_encounter(
    session: AsyncSession, *, session_id: UUID, learner_id: UUID, case_id: UUID
) -> EncounterCreated:
    """Select a case into a session as its next encounter."""

    await get_owned_session(session, session_id=session_id, learner_id=learner_id)

    case = (
        await session.exec(
            select(Case).where(
                Case.id == case_id,
                Case.status == CaseStatus.PUBLISHED,
                Case.case_type == CaseType.HARM,
            )
        )
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

    record = CaseEncounter(
        session_id=session_id, case_id=case_id, sequence_no=len(existing) + 1
    )
    session.add(record)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        # Either the 3-encounter cap (sequence_no would exceed 3) or a
        # concurrent request that claimed this sequence_no first. The database
        # settles both, so no locking is needed to read the count above.
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
    encounter_id: UUID,
    learner_id: UUID,
    pattern: Pattern,
    gate: Gate,
    framing_answers: dict[str, Any],
) -> CommitmentCreated:
    """Store the learner's interpretation of an encounter.

    One commitment per encounter for now. This is enforced here rather than by
    a unique constraint on purpose: `Commitment` is keyed on
    (case_encounter_id, sequence_no) so a future group re-vote can add a second
    row without overwriting the first.
    """

    encounter = await get_owned_encounter(
        session, encounter_id=encounter_id, learner_id=learner_id
    )

    already_committed = (
        await session.exec(
            select(Commitment).where(Commitment.case_encounter_id == encounter.id)
        )
    ).first()
    if already_committed is not None:
        raise ConflictError("Encounter already has a commitment")

    record = Commitment(
        case_encounter_id=encounter.id,
        sequence_no=1,
        pattern=pattern,
        gate=gate,
        framing_answers=framing_answers,
    )
    session.add(record)
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

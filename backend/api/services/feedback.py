from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Case, Commitment, FeedbackRecord
from api.models.enums import Domain, Gate, MatchResult, Pattern
from api.services.encounters import get_owned_encounter
from api.services.errors import ConflictError, NotFoundError
from api.services.sessions import get_owned_session, require_student_route


class RevealedCase(BaseModel):
    """The case with its answer key. Only ever returned by the reveal."""

    id: UUID
    title: str
    domain: Domain
    full_narrative: str
    main_path_pattern: Pattern
    main_path_gate: Gate
    source_references: list[str]


class RevealedCommitment(BaseModel):
    """What the learner committed to, echoed back next to the verdict."""

    pattern: Pattern
    gate: Gate


class RevealResponse(BaseModel):
    """The full reveal for one encounter."""

    feedback_record_id: UUID
    match_result: MatchResult
    revealed_at: datetime
    commitment: RevealedCommitment
    case: RevealedCase


def compute_match_result(*, commitment: Commitment, case: Case) -> MatchResult:
    """Compare a commitment against the case's main path."""

    pattern_matches = commitment.pattern == case.main_path_pattern
    gate_matches = commitment.gate == case.main_path_gate

    if pattern_matches and gate_matches:
        return MatchResult.MATCH
    if pattern_matches or gate_matches:
        return MatchResult.PARTIAL_MATCH
    return MatchResult.MISMATCH


async def reveal_encounter(
    session: AsyncSession, *, encounter_id: UUID, learner_id: UUID
) -> RevealResponse:
    """Return the encounter's reveal, computing it only the first time.

    The verdict a learner sees must never change under them, so an existing
    `FeedbackRecord` is returned untouched -- never recomputed, never
    restamped.
    """

    encounter = await get_owned_encounter(
        session, encounter_id=encounter_id, learner_id=learner_id
    )
    owned_session = await get_owned_session(
        session, session_id=encounter.session_id, learner_id=learner_id
    )
    require_student_route(owned_session.route)

    case = await session.get(Case, encounter.case_id)
    if case is None:
        raise NotFoundError("Case not found")

    commitment = (
        await session.exec(
            select(Commitment)
            .where(Commitment.case_encounter_id == encounter_id)
            .order_by(desc(col(Commitment.sequence_no)))
        )
    ).first()
    if commitment is None:
        raise ConflictError("Encounter has no commitment to reveal")

    # Snapshot the ORM-derived parts of the response now. The race path below
    # rolls back, and a rollback expires every object loaded above regardless
    # of expire_on_commit -- reading them afterwards would attempt implicit IO
    # that async SQLAlchemy cannot perform during attribute access.
    revealed_commitment = RevealedCommitment(
        pattern=commitment.pattern, gate=commitment.gate
    )
    revealed_case = RevealedCase(
        id=case.id,
        title=case.title,
        domain=case.domain,
        full_narrative=case.full_narrative,
        main_path_pattern=case.main_path_pattern,
        main_path_gate=case.main_path_gate,
        source_references=case.source_references,
    )

    def _respond(record: FeedbackRecord) -> RevealResponse:
        return RevealResponse(
            feedback_record_id=record.id,
            match_result=record.match_result,
            revealed_at=record.revealed_at,
            commitment=revealed_commitment,
            case=revealed_case,
        )

    existing = await _find_record(session, encounter_id=encounter_id)
    if existing is not None:
        return _respond(existing)

    record = FeedbackRecord(
        case_encounter_id=encounter_id,
        commitment_id=commitment.id,
        match_result=compute_match_result(commitment=commitment, case=case),
    )
    session.add(record)
    try:
        await session.flush()
    except IntegrityError:
        # A concurrent reveal inserted first. Roll back before querying: the
        # session cannot run further statements while the failed transaction
        # is open.
        await session.rollback()
        existing = await _find_record(session, encounter_id=encounter_id)
        if existing is None:
            # Not the unique violation we expected, so this is a real fault.
            raise
        return _respond(existing)
    await session.commit()

    return _respond(record)


async def _find_record(
    session: AsyncSession, *, encounter_id: UUID
) -> FeedbackRecord | None:
    return (
        await session.exec(
            select(FeedbackRecord).where(
                FeedbackRecord.case_encounter_id == encounter_id
            )
        )
    ).first()

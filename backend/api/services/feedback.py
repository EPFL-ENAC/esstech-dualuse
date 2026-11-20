from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col, desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Case, CaseEncounter, Commitment, FeedbackRecord
from api.models.enums import Domain, Gate, MatchResult, Pattern
from api.services.errors import ConflictError, NotFoundError
from api.services.persistence import insert_once


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
    session: AsyncSession, *, encounter: CaseEncounter
) -> RevealResponse:
    """Return the encounter's reveal, computing it only the first time.

    The verdict a learner sees must never change under them, so an existing
    `FeedbackRecord` is returned untouched -- never recomputed, never
    restamped.
    """

    encounter_id = encounter.id

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

    # Copied out now: insert_once may roll back, which expires every ORM
    # object loaded above.
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
    new_record = FeedbackRecord(
        case_encounter_id=encounter_id,
        commitment_id=commitment.id,
        match_result=compute_match_result(commitment=commitment, case=case),
    )

    async def find_existing() -> FeedbackRecord | None:
        return (
            await session.exec(
                select(FeedbackRecord).where(
                    FeedbackRecord.case_encounter_id == encounter_id
                )
            )
        ).first()

    record = await find_existing()
    if record is None:
        record, created = await insert_once(session, new_record, find_existing)
        if created:
            await session.commit()

    return RevealResponse(
        feedback_record_id=record.id,
        match_result=record.match_result,
        revealed_at=record.revealed_at,
        commitment=revealed_commitment,
        case=revealed_case,
    )

from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Case, CaseEncounter, Session
from api.models.enums import CaseStatus, CaseType, Domain

CANDIDATE_LIMIT = 3


class CaseCandidate(BaseModel):
    """A case as shown before the learner commits.

    Deliberately narrower than `Case`: `full_narrative`, `main_path_pattern`
    and `main_path_gate` are the answer key, and `source_references` can hint
    at it, so none of them appear until the reveal. Keeping the anti-spoiler
    rule in one schema means endpoints cannot leak it one field at a time.
    """

    id: UUID
    title: str
    area: str
    domain: Domain
    case_type: CaseType
    narrative_until_crossroads: str


def to_candidate(case: Case) -> CaseCandidate:
    """Project a case down to what a learner may see before committing."""

    return CaseCandidate(
        id=case.id,
        title=case.title,
        area=case.area,
        domain=case.domain,
        case_type=case.case_type,
        narrative_until_crossroads=case.narrative_until_crossroads,
    )


async def list_candidate_cases(
    session: AsyncSession, *, learner_id: UUID
) -> list[CaseCandidate]:
    """Published harm cases this learner has not met in any of their sessions."""

    encountered = (
        select(CaseEncounter.case_id)
        .join(Session, onclause=col(Session.id) == col(CaseEncounter.session_id))
        .where(Session.learner_id == learner_id)
    )
    candidates = (
        await session.exec(
            select(Case)
            .where(
                Case.status == CaseStatus.PUBLISHED,
                Case.case_type == CaseType.HARM,
                col(Case.id).not_in(encountered),
            )
            # Ordered so repeated calls are stable rather than arbitrary.
            .order_by(col(Case.created_at), col(Case.id))
            .limit(CANDIDATE_LIMIT)
        )
    ).all()

    return [to_candidate(case) for case in candidates]

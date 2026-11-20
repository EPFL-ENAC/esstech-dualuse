from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Case, CaseTaggedFunction, ComparisonSetCase
from api.models.enums import (
    Domain,
    Form,
    Function,
    Gate,
    InclusionReason,
    Pattern,
)
from api.services.errors import NotFoundError
from api.services.researcher import (
    find_predictions,
    require_comparison_set,
)


class ResearcherCaseDetail(BaseModel):
    """One case from a session's comparison set, with why it was included.

    Anti-spoiler: full_narrative, main_path_pattern, main_path_gate and
    source_references are the answer key, so they stay None until the
    session has submitted its prediction.
    """

    case_id: UUID
    title: str
    area: str
    narrative_until_crossroads: str
    domain: Domain
    functions: list[Function]
    forms: list[Form]
    inclusion_reason: InclusionReason
    full_narrative: str | None = None
    main_path_pattern: Pattern | None = None
    main_path_gate: Gate | None = None
    source_references: list[str] | None = None


async def get_researcher_case_detail(
    session: AsyncSession, *, session_id: UUID, case_id: UUID
) -> ResearcherCaseDetail:
    """Return one case from a session's comparison set, gated on prediction.

    A case outside this session's set is a 404, never revealing whether it
    exists at all.
    """

    comparison_set = await require_comparison_set(session, session_id=session_id)

    row = (
        await session.exec(
            select(ComparisonSetCase, Case)
            .join(Case, col(Case.id) == col(ComparisonSetCase.case_id))
            .where(
                ComparisonSetCase.comparison_set_id == comparison_set.id,
                ComparisonSetCase.case_id == case_id,
            )
        )
    ).first()
    if row is None:
        raise NotFoundError("Case not found")
    membership, case = row

    # ty stub gap: rows of a select over an sa_enum column are not
    # inferred as Function, though that is the runtime value.
    functions: list[Function] = (
        await session.exec(
            select(CaseTaggedFunction.function).where(
                CaseTaggedFunction.case_id == case_id
            )
        )
    ).all()  # type: ignore

    is_revealed = bool(await find_predictions(session, session_id=session_id))

    return ResearcherCaseDetail(
        case_id=case.id,
        title=case.title,
        area=case.area,
        narrative_until_crossroads=case.narrative_until_crossroads,
        domain=case.domain,
        functions=functions,
        forms=case.forms,
        inclusion_reason=membership.inclusion_reason,
        full_narrative=case.full_narrative if is_revealed else None,
        main_path_pattern=case.main_path_pattern if is_revealed else None,
        main_path_gate=case.main_path_gate if is_revealed else None,
        source_references=case.source_references if is_revealed else None,
    )

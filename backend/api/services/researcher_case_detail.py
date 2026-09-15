from uuid import UUID

from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Case, CaseTaggedFunction, ComparisonSetCase
from api.models.enums import (
    Domain,
    Form,
    Function,
    Gate,
    InclusionReason,
    Pattern,
    SessionRoute,
)
from api.services.errors import ConflictError, NotFoundError
from api.services.researcher import (
    find_comparison_set,
    find_predictions,
    require_researcher_route,
)


class ResearcherCaseDetail(BaseModel):
    """One case from a session's comparison set, with why it was included.

    Deliberately narrower pre-prediction: main_path_pattern,
    main_path_gate, full_narrative, and source_references are the answer
    key, gated on find_predictions(...) being non-empty for this session
    -- the same anti-spoiler rule Student's CaseCandidate/RevealedCase
    split enforces (api/services/cases.py, api/services/feedback.py), kept
    here as one model with optional gated fields rather than two classes.
    Student's split exists because it has two separate endpoints for two
    distinct moments (browse-time, one-shot reveal); this is one
    revisitable endpoint whose content depends on session state at call
    time, the same shape as ResearcherSessionReport.
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
    session: AsyncSession, *, session_id: UUID, case_id: UUID, route: SessionRoute
) -> ResearcherCaseDetail:
    """Return one case from a session's comparison set, gated on prediction.

    404s if case_id is not among this session's ComparisonSetCase rows --
    never reveals whether the case exists at all outside the caller's own
    set, the same "ownership hides existence" discipline as every other
    404 in this project (e.g. encounters.py's Case-not-found).
    """

    require_researcher_route(route)

    comparison_set = await find_comparison_set(session, session_id=session_id)
    if comparison_set is None:
        raise ConflictError("Session has no comparison set to look up this case in")

    membership = (
        await session.exec(
            select(ComparisonSetCase).where(
                ComparisonSetCase.comparison_set_id == comparison_set.id,
                ComparisonSetCase.case_id == case_id,
            )
        )
    ).first()
    if membership is None:
        raise NotFoundError("Case not found")

    # Guaranteed to exist: ComparisonSetCase.case_id is a foreign key to
    # case.id, so a row that just matched above always has a real Case.
    case = (await session.exec(select(Case).where(Case.id == case_id))).first()
    assert case is not None

    # ty infers this select(SomeModel.enum_column)'s rows as an
    # unspecialized Sequence rather than plain Function -- the same stub
    # gap get_pattern_distribution's own comment documents (researcher.py),
    # not a real type error.
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
